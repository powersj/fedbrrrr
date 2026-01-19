# Indicator calculators module
from .base import BaseCalculator
from .buffett_indicator import BuffettIndicatorCalculator
from .yield_curves import YieldCurve10Y2YCalculator, YieldCurve10Y3MCalculator
from .sahm_rule import SahmRuleCalculator
from .fed_balance_sheet import FedBalanceSheetCalculator
from .m2_growth import M2GrowthCalculator
from .consumer_confidence import ConsumerConfidenceCalculator
from .mortgage_affordability import MortgageAffordabilityCalculator
from .credit_card_delinquency import CreditCardDelinquencyCalculator
from .debt_service_ratio import DebtServiceRatioCalculator
from .real_wage_growth import RealWageGrowthCalculator
from .personal_savings import PersonalSavingsCalculator
from .rent_burden import RentBurdenCalculator
from .food_burden import FoodBurdenCalculator

# All calculator classes
ALL_CALCULATORS = [
    # Economy indicators
    BuffettIndicatorCalculator,
    YieldCurve10Y2YCalculator,
    YieldCurve10Y3MCalculator,
    SahmRuleCalculator,
    FedBalanceSheetCalculator,
    M2GrowthCalculator,
    ConsumerConfidenceCalculator,
    # Household indicators
    MortgageAffordabilityCalculator,
    CreditCardDelinquencyCalculator,
    DebtServiceRatioCalculator,
    RealWageGrowthCalculator,
    PersonalSavingsCalculator,
    RentBurdenCalculator,
    FoodBurdenCalculator,
]
