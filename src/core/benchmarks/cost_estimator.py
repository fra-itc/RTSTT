"""
Cost estimation for STT providers.

Calculates and compares costs across cloud providers and local hosting.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PricingModel(Enum):
    """Pricing model type."""
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    PER_REQUEST = "per_request"
    FREE = "free"


@dataclass
class CostBreakdown:
    """Detailed cost breakdown."""
    provider_name: str
    model_name: str
    pricing_model: PricingModel

    # Costs in USD
    cost_per_minute: float = 0.0
    cost_per_hour: float = 0.0
    cost_per_1k_minutes: float = 0.0
    cost_per_100_hours: float = 0.0

    # Additional costs
    monthly_subscription: float = 0.0  # Fixed monthly cost
    free_tier_minutes: float = 0.0  # Free tier allocation

    # Local hosting costs (if applicable)
    gpu_power_cost_per_hour: float = 0.0  # Electricity cost
    gpu_amortization_per_hour: float = 0.0  # Hardware amortization


class CostEstimator:
    """
    Estimate and compare costs across STT providers.

    Includes both cloud API costs and local hosting costs (electricity, hardware).
    """

    # Pricing data (as of 2024, subject to change)
    PROVIDER_PRICING = {
        "OpenAI": {
            "Whisper-1": {
                "model": PricingModel.PER_MINUTE,
                "cost_per_minute": 0.006,  # $0.006 per minute
            }
        },
        "Deepgram": {
            "Nova-3": {
                "model": PricingModel.PER_MINUTE,
                "cost_per_minute": 0.0043,  # $0.0043 per minute
                "free_tier_minutes": 200,  # 200 free minutes per month
            },
            "Nova-2": {
                "model": PricingModel.PER_MINUTE,
                "cost_per_minute": 0.0036,
                "free_tier_minutes": 200,
            }
        },
        "AssemblyAI": {
            "Universal-2": {
                "model": PricingModel.PER_HOUR,
                "cost_per_hour": 0.15,  # $0.15 per hour
                "free_tier_minutes": 300,  # 5 hours free per month
            }
        },
        "Mistral": {
            "Voxtral": {
                "model": PricingModel.PER_MINUTE,
                "cost_per_minute": 0.005,  # Estimated
            }
        },
        "Google": {
            "Chirp": {
                "model": PricingModel.PER_MINUTE,
                "cost_per_minute": 0.004,  # $0.004 per minute for standard
                "free_tier_minutes": 60,  # 60 minutes free per month
            }
        },
        "Azure": {
            "Speech": {
                "model": PricingModel.PER_HOUR,
                "cost_per_hour": 1.0,  # $1 per hour for standard
                "free_tier_minutes": 300,  # 5 hours free per month
            }
        },
        # Local models - hardware and electricity costs
        "Whisper": {
            "Large-v3": {
                "model": PricingModel.FREE,
                "cost_per_minute": 0.0,
                "gpu_power_cost_per_hour": 0.05,  # ~300W GPU at $0.15/kWh
                "gpu_amortization_per_hour": 0.17,  # RTX 5080 $1500 amortized over 3 years
            }
        },
        "Voxtral": {
            "Mini-3B": {
                "model": PricingModel.FREE,
                "cost_per_minute": 0.0,
                "gpu_power_cost_per_hour": 0.03,  # Lighter model
                "gpu_amortization_per_hour": 0.17,
            }
        },
        "NVIDIA": {
            "Parakeet-0.6B": {
                "model": PricingModel.FREE,
                "cost_per_minute": 0.0,
                "gpu_power_cost_per_hour": 0.02,  # Very light model
                "gpu_amortization_per_hour": 0.17,
            }
        },
        "WhisperLiveKit": {
            "Base": {
                "model": PricingModel.FREE,
                "cost_per_minute": 0.0,
                "gpu_power_cost_per_hour": 0.04,
                "gpu_amortization_per_hour": 0.17,
            }
        },
        "Vosk": {
            "Lightweight": {
                "model": PricingModel.FREE,
                "cost_per_minute": 0.0,
                "gpu_power_cost_per_hour": 0.01,  # CPU-based
                "gpu_amortization_per_hour": 0.0,  # No GPU needed
            }
        },
        "RealtimeSTT": {
            "Base": {
                "model": PricingModel.FREE,
                "cost_per_minute": 0.0,
                "gpu_power_cost_per_hour": 0.03,
                "gpu_amortization_per_hour": 0.17,
            }
        },
    }

    def __init__(
        self,
        electricity_rate_per_kwh: float = 0.15,
        gpu_cost: float = 1500.0,
        gpu_lifetime_years: float = 3.0
    ):
        """
        Initialize CostEstimator.

        Args:
            electricity_rate_per_kwh: Cost of electricity in USD per kWh
            gpu_cost: Cost of GPU hardware in USD
            gpu_lifetime_years: Expected GPU lifetime for amortization
        """
        self.electricity_rate = electricity_rate_per_kwh
        self.gpu_cost = gpu_cost
        self.gpu_lifetime_years = gpu_lifetime_years

        logger.info(
            f"CostEstimator initialized (electricity: ${electricity_rate_per_kwh}/kWh, "
            f"GPU: ${gpu_cost}, lifetime: {gpu_lifetime_years} years)"
        )

    def get_cost_breakdown(
        self,
        provider_name: str,
        model_name: str
    ) -> Optional[CostBreakdown]:
        """
        Get cost breakdown for a specific provider and model.

        Args:
            provider_name: Provider name
            model_name: Model name

        Returns:
            CostBreakdown or None if not found
        """
        provider_data = self.PROVIDER_PRICING.get(provider_name)
        if not provider_data:
            logger.warning(f"Provider '{provider_name}' not found in pricing data")
            return None

        model_data = provider_data.get(model_name)
        if not model_data:
            logger.warning(f"Model '{model_name}' not found for provider '{provider_name}'")
            return None

        breakdown = CostBreakdown(
            provider_name=provider_name,
            model_name=model_name,
            pricing_model=model_data["model"],
            cost_per_minute=model_data.get("cost_per_minute", 0.0),
            cost_per_hour=model_data.get("cost_per_hour", 0.0),
            free_tier_minutes=model_data.get("free_tier_minutes", 0.0),
            gpu_power_cost_per_hour=model_data.get("gpu_power_cost_per_hour", 0.0),
            gpu_amortization_per_hour=model_data.get("gpu_amortization_per_hour", 0.0),
        )

        # Calculate derived costs
        if breakdown.cost_per_minute > 0:
            breakdown.cost_per_hour = breakdown.cost_per_minute * 60
        elif breakdown.cost_per_hour > 0:
            breakdown.cost_per_minute = breakdown.cost_per_hour / 60

        breakdown.cost_per_1k_minutes = breakdown.cost_per_minute * 1000
        breakdown.cost_per_100_hours = breakdown.cost_per_hour * 100

        return breakdown

    def compare_costs(
        self,
        audio_hours: float,
        providers: Optional[List[tuple]] = None
    ) -> List[Dict]:
        """
        Compare costs across multiple providers for a given amount of audio.

        Args:
            audio_hours: Amount of audio to process in hours
            providers: List of (provider_name, model_name) tuples. None for all.

        Returns:
            List of cost comparison dicts, sorted by total cost
        """
        if providers is None:
            # Use all providers
            providers = []
            for prov_name, models in self.PROVIDER_PRICING.items():
                for model_name in models.keys():
                    providers.append((prov_name, model_name))

        comparisons = []

        for provider_name, model_name in providers:
            breakdown = self.get_cost_breakdown(provider_name, model_name)
            if not breakdown:
                continue

            audio_minutes = audio_hours * 60

            # Calculate total cost
            if breakdown.pricing_model == PricingModel.FREE:
                # For local models, include electricity and amortization
                api_cost = 0.0
                infrastructure_cost = (
                    breakdown.gpu_power_cost_per_hour +
                    breakdown.gpu_amortization_per_hour
                ) * audio_hours
                total_cost = infrastructure_cost
            else:
                # Cloud API cost
                api_cost = breakdown.cost_per_minute * audio_minutes
                infrastructure_cost = 0.0
                total_cost = api_cost

            # Account for free tier
            if breakdown.free_tier_minutes > 0 and audio_minutes <= breakdown.free_tier_minutes:
                api_cost = 0.0
                total_cost = infrastructure_cost

            comparisons.append({
                "provider_name": provider_name,
                "model_name": model_name,
                "pricing_model": breakdown.pricing_model.value,
                "audio_hours": audio_hours,
                "api_cost": api_cost,
                "infrastructure_cost": infrastructure_cost,
                "total_cost": total_cost,
                "cost_per_hour": total_cost / audio_hours if audio_hours > 0 else 0,
                "free_tier_minutes": breakdown.free_tier_minutes,
            })

        # Sort by total cost
        comparisons.sort(key=lambda x: x["total_cost"])

        return comparisons

    def calculate_breakeven(
        self,
        cloud_provider: str,
        cloud_model: str,
        local_provider: str,
        local_model: str
    ) -> Optional[float]:
        """
        Calculate break-even point (in hours) between cloud and local.

        Args:
            cloud_provider: Name of cloud provider
            cloud_model: Name of cloud model
            local_provider: Name of local provider
            local_model: Name of local model

        Returns:
            Break-even hours, or None if not applicable
        """
        cloud_breakdown = self.get_cost_breakdown(cloud_provider, cloud_model)
        local_breakdown = self.get_cost_breakdown(local_provider, local_model)

        if not cloud_breakdown or not local_breakdown:
            return None

        # Cloud cost per hour (API)
        cloud_cost_per_hour = cloud_breakdown.cost_per_hour

        # Local cost per hour (electricity + amortization)
        local_cost_per_hour = (
            local_breakdown.gpu_power_cost_per_hour +
            local_breakdown.gpu_amortization_per_hour
        )

        if cloud_cost_per_hour <= local_cost_per_hour:
            # Cloud is always cheaper
            return None

        # Break-even calculation
        # cloud_cost_per_hour * hours = local_cost_per_hour * hours + gpu_cost
        # Simplified: when does cumulative cloud cost = initial GPU investment
        if cloud_cost_per_hour > 0:
            breakeven_hours = self.gpu_cost / (cloud_cost_per_hour - local_cost_per_hour)
            return breakeven_hours

        return None

    def estimate_monthly_cost(
        self,
        provider_name: str,
        model_name: str,
        hours_per_day: float
    ) -> Dict:
        """
        Estimate monthly cost for a given usage pattern.

        Args:
            provider_name: Provider name
            model_name: Model name
            hours_per_day: Hours of audio processed per day

        Returns:
            Dict with monthly cost estimate
        """
        breakdown = self.get_cost_breakdown(provider_name, model_name)
        if not breakdown:
            return {}

        monthly_hours = hours_per_day * 30
        monthly_minutes = monthly_hours * 60

        # Calculate monthly cost
        if breakdown.pricing_model == PricingModel.FREE:
            monthly_api_cost = 0.0
            monthly_infrastructure_cost = (
                breakdown.gpu_power_cost_per_hour +
                breakdown.gpu_amortization_per_hour
            ) * monthly_hours
        else:
            # Account for free tier
            billable_minutes = max(0, monthly_minutes - breakdown.free_tier_minutes)
            monthly_api_cost = breakdown.cost_per_minute * billable_minutes
            monthly_infrastructure_cost = 0.0

        total_monthly_cost = monthly_api_cost + monthly_infrastructure_cost

        return {
            "provider_name": provider_name,
            "model_name": model_name,
            "hours_per_day": hours_per_day,
            "monthly_hours": monthly_hours,
            "monthly_api_cost": monthly_api_cost,
            "monthly_infrastructure_cost": monthly_infrastructure_cost,
            "total_monthly_cost": total_monthly_cost,
            "free_tier_minutes": breakdown.free_tier_minutes,
        }
