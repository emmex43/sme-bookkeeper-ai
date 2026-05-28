import json
import logging
from datetime import timedelta
from decimal import Decimal

from google import genai
from google.genai import types
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from .models import LedgerEntry, MerchantProfile

logger = logging.getLogger(__name__)

_gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

_ADVICE_PROMPT_TEMPLATE = """
You are a financial coach for Nigerian small business owners.
Given the 7-day financial summary below, give EXACTLY 3 sentences of specific, 
actionable advice the merchant should act on THIS WEEK.
Rules:
- Never repeat or narrate the numbers back to the merchant.
- Each sentence must recommend a specific action.
- Start directly with the first sentence. Do NOT use introductory titles, labels, asterisks, bolding, or markdown.
- Keep each sentence under 25 words.
- Use ₦ for currency. Use short forms like ₦6M, ₦353K.

Merchant Financial Summary (last 7 days):
{financial_summary}
""".strip()

_LOAN_PROMPT_TEMPLATE = """
You are the Chief Credit Officer for a Nigerian SME lending platform.
The merchant is requesting a loan of ₦{requested_amount:,.2f}.

Merchant Financial Summary (Last 30 days):
{financial_summary}

DECISION RULES:
1. If the Credit Score is below 600, REJECT.
2. If the requested loan is greater than 50% of their 30_day_revenue, REJECT.
3. Otherwise, APPROVE.

You MUST respond strictly in JSON format matching this schema:
{{"status": "APPROVED" or "REJECTED", "reason": "1-2 sentences explaining exactly why based on their numbers."}}
""".strip()

_FALLBACK_ADVICE = (
    "Your AI advisor is currently unavailable. "
    "Please check back shortly for updated financial insights."
)


class FintechAIService:

    @staticmethod
    def generate_financial_advice(merchant_id: int) -> str:
        try:
            summary = FintechAIService._build_financial_summary(merchant_id)
            prompt = _ADVICE_PROMPT_TEMPLATE.format(financial_summary=summary)
            response = _gemini_client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4, max_output_tokens=800),
            )
            return response.text.strip()
        except Exception:
            logger.exception("generate_financial_advice error")
            return _FALLBACK_ADVICE

    @staticmethod
    def evaluate_loan(merchant_id: int, requested_amount: float) -> dict:
        """Evaluates a loan application using Gemini and returns a JSON decision."""
        try:
            merchant = MerchantProfile.objects.get(pk=merchant_id)
            thirty_days_ago = timezone.now() - timedelta(days=30)

            recent_entries = LedgerEntry.objects.filter(
                merchant_id=merchant_id, transaction_date__gte=thirty_days_ago
            )

            rev_total = recent_entries.filter(transaction_type='CR').aggregate(
                total=Sum("amount"))["total"] or Decimal("0.00")
            exp_total = recent_entries.filter(transaction_type='DR').aggregate(
                total=Sum("amount"))["total"] or Decimal("0.00")

            summary = {
                "business_name": merchant.business_name,
                "credit_score": merchant.credit_score,
                "30_day_revenue": float(rev_total),
                "30_day_expenses": float(exp_total),
                "net_profit": float(rev_total - exp_total)
            }

            prompt = _LOAN_PROMPT_TEMPLATE.format(
                requested_amount=requested_amount,
                financial_summary=json.dumps(summary)
            )

            response = _gemini_client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",  # Forces AI to return clean JSON
                ),
            )

            return json.loads(response.text)

        except Exception as e:
            logger.exception("Loan evaluation error")
            return {"status": "ERROR", "reason": "Unable to process loan application at this time."}

    @staticmethod
    def _build_financial_summary(merchant_id: int) -> str:
        merchant = MerchantProfile.objects.get(pk=merchant_id)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_entries = LedgerEntry.objects.filter(
            merchant_id=merchant_id, transaction_date__gte=seven_days_ago)

        total_revenue = recent_entries.filter(transaction_type='CR').aggregate(
            total=Sum("amount"))["total"] or Decimal("0.00")
        total_expenses = recent_entries.filter(transaction_type='DR').aggregate(
            total=Sum("amount"))["total"] or Decimal("0.00")

        summary_dict = {
            "merchant_name": merchant.business_name,
            "credit_score": merchant.credit_score,
            "total_revenue_ngn": f"₦{total_revenue:,.0f}",
            "total_expenses_ngn": f"₦{total_expenses:,.0f}",
        }
        return json.dumps(summary_dict, separators=(",", ":"))
