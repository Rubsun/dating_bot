class ProfileRatingCalculator:
    BASE_RATING = 800
    MAX_BONUS = 200

    WEIGHTS = {
        # 'profile_completeness': 0.30,
        'photo_quality': 0.25,
        'description_quality': 0.20,
    }

    @classmethod
    def calculate(cls, profile_data):
        score = 0

        # score += profile_data.get('profile_completeness', 0) * cls.WEIGHTS['profile_completeness']
        score += (1 if profile_data.photo_file_id else 0) * cls.WEIGHTS['photo_quality']
        score += (1 if profile_data.bio else 0) * cls.WEIGHTS['description_quality']
        score *= (1 if profile_data.gender == 'male' else 0.9)

        # Применяем максимальный бонус
        bonus = cls.MAX_BONUS * min(max(score, 0), 1)  # Ограничение 0-1
        return round(cls.BASE_RATING + bonus)

    @classmethod
    def update_calculation(cls, profile_data):
        rating = profile_data.rating

        new_rating = 0
        new_rating += (1 if profile_data.photo_file_id else 0) * cls.WEIGHTS['photo_quality'] * rating
        new_rating += (1 if profile_data.bio else 0) * cls.WEIGHTS['description_quality'] * rating

        return rating + new_rating

class RatingService:
    def __init__(self, calculator: ProfileRatingCalculator, k=32, min_rating=100):
        self.calculator = calculator
        self.ratings = {}
        self.k = k
        self.min_rating = min_rating

    async def init_rating(self, profile_data):
        initial_rating = self.calculator.calculate(profile_data)

        return round(initial_rating, 2)

    # async def get_rating(self, user_id):
    #     profile = await self.rating_repo.get_rating_by_profile_id(user_id)
    #     return profile
    #
    def update_rating(self, profile_data):
        updating_rating = self.calculator.update_calculation(profile_data)

        return updating_rating

    @staticmethod
    def _expected_score(rating_a, rating_b):
        return round(1 / (1 + 10 ** ((rating_b - rating_a) / 400)), 2)

    async def add_like(self, rater_rating, rated_rating):
        expected = self._expected_score(rater_rating, rated_rating)
        delta = self.k * (1 - expected)
        return round(delta, 2)

    async def add_dislike(self, rater_rating, rated_rating):
        expected = self._expected_score(rater_rating, rated_rating)
        delta = self.k * (-expected)
        return round(delta, 2)

    # def get_top_users(self, limit=10):
    #     sorted_users = sorted(self.ratings.items(), key=lambda x: -x[1])
    #     return sorted_users[:limit]