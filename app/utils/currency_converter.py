from typing import Optional

from app.core.config import Settings

settings = Settings()


import httpx


class CurrencyConverter:
    BASE_URL = "https://api.exconvert.com/convert"
    ACCESS_KEY: str = settings.CURRENCY_API_KEY

    @staticmethod
    async def convert_amount(
        from_currency: str, to_currency: str, amount: float
    ) -> Optional[float]:
        """
        Convert amount from one currency to another using exconvert API.

        Args:
            from_currency: Source currency code (e.g., 'EGP')
            to_currency: Target currency code (e.g., 'USD')
            amount: Amount to convert

        Returns:
            Converted amount rounded to 1 decimal place, or None if conversion fails
        """
        if from_currency == to_currency:
            return round(amount, 1)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    CurrencyConverter.BASE_URL,
                    params={
                        "from": from_currency,
                        "to": to_currency,
                        "amount": str(amount),
                        "access_key": CurrencyConverter.ACCESS_KEY,
                    },
                )
                response.raise_for_status()
                data = response.json()

                if "result" in data and to_currency in data["result"]:
                    converted = data["result"][to_currency]
                    return round(float(converted), 1)
                else:
                    print(f"Unexpected API response: {data}")
                    return None

        except Exception as e:
            print(f"Currency conversion failed: {e}")
            return None

    @staticmethod
    def convert_amount_sync(
        from_currency: str, to_currency: str, amount: float
    ) -> Optional[float]:
        """
        Synchronous version of convert_amount for use in non-async contexts.
        """
        if from_currency == to_currency:
            return round(amount, 1)

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    CurrencyConverter.BASE_URL,
                    params={
                        "from": from_currency,
                        "to": to_currency,
                        "amount": str(amount),
                        "access_key": CurrencyConverter.ACCESS_KEY,
                    },
                )
                response.raise_for_status()
                data = response.json()

                if "result" in data and to_currency in data["result"]:
                    converted = data["result"][to_currency]
                    return round(float(converted), 1)
                else:
                    print(f"Unexpected API response: {data}")
                    return None

        except Exception as e:
            print(f"Currency conversion failed: {e}")
            return None
