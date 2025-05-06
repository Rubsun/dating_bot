class ProfileRatingCalculator:
    BASE_RATING = 800
    MAX_BONUS = 200

    WEIGHTS = {
        'profile_completeness': 0.30,
        'photo_quality': 0.25,
        'description_quality': 0.20,
    }

    @classmethod
    async def calculate(cls, profile_data):
        score = 0

        score += ((0.25 if profile_data.first_name else 0) + (0.25 if profile_data.last_name else 0) + (0.25 if profile_data.age else 0) + (0.25 if profile_data.city else 0)) * cls.WEIGHTS['profile_completeness']
        score += (1 if profile_data.bio else 0) * cls.WEIGHTS['description_quality']
        score *= (1 if profile_data.gender == 'male' else 0.9)

        if len(profile_data.photo_file_ids) == 3:
            score += (1 * cls.WEIGHTS['photo_quality'])
        elif len(profile_data.photo_file_ids) == 2:
            score += (0.5 * cls.WEIGHTS['photo_quality'])
        elif len(profile_data.photo_file_ids) == 1:
            score += (0.2 * cls.WEIGHTS['photo_quality'])
        else:
            score += 0

        bonus = cls.MAX_BONUS * min(max(score, 0), 1.5)
        return round(cls.BASE_RATING + bonus)

    @classmethod
    async def update_calculation(cls, old_rating, profile_data):
        rating = old_rating

        new_rating = 0
        new_rating += (1 if profile_data['photo_file_id'] else 0) * cls.WEIGHTS['photo_quality'] * rating
        new_rating += (1 if profile_data['bio'] else 0) * cls.WEIGHTS['description_quality'] * rating

        return rating + new_rating

    @classmethod
    async def update_match(cls, old_rating, match_rating):
        rating_adjustment = 0.05
        base_match_bonus = 25

        rating_diff = match_rating - old_rating
        adjustment = rating_diff * rating_adjustment
        return old_rating + base_match_bonus + adjustment

    @classmethod
    async def update_ref(cls, old_rating):
        base_ref_bonus = 50
        max_ref_bonus = 250

        bonus = base_ref_bonus / (1 + old_rating / 1000)
        return min(old_rating + bonus, old_rating + max_ref_bonus)

    @classmethod
    async def update_chat(cls, old_rating, chat_rating):
        activity_bonus = 0.1
        base_chat_bonus = 10

        mutual_bonus = (old_rating + chat_rating) * activity_bonus
        return old_rating + base_chat_bonus + mutual_bonus


class RatingService:
    def __init__(self, calculator: ProfileRatingCalculator, k=32, min_rating=100):
        self.calculator = calculator
        self.ratings = {}
        self.k = k
        self.min_rating = min_rating

    async def init_rating(self, profile_data):
        initial_rating = await self.calculator.calculate(profile_data)

        return round(initial_rating, 2)

    async def update_rating(self, old_rating, profile_data):
        updating_rating = await self.calculator.update_calculation(old_rating, profile_data)

        return round(updating_rating, 2)

    @staticmethod
    async def _expected_score(rating_a, rating_b):
        return round(1 / (1 + 10 ** ((rating_b - rating_a) / 400)), 2)

    async def add_like(self, rater_rating, rated_rating):
        expected = await self._expected_score(rater_rating, rated_rating)
        delta = self.k * (1 - expected)
        return round(delta, 2)

    async def add_dislike(self, rater_rating, rated_rating):
        expected = await self._expected_score(rater_rating, rated_rating)
        delta = self.k * (-expected)
        return round(delta, 2)

    async def match(self, rating1, rating2):
        old_rating1 = rating1.rating_score
        old_rating2 = rating2.rating_score

        new_rating1 = await self.calculator.update_match(old_rating1, old_rating2)
        new_rating2 = await self.calculator.update_match(old_rating2, old_rating1)

        return {
            'user1': round(max(new_rating1, self.min_rating), 2),
            'user2': round(max(new_rating2, self.min_rating), 2)
        }

    async def chat(self, rating1, rating2):
        old_rating1 = rating1.rating_score
        old_rating2 = rating2.rating_score

        new_rating2 = await self.calculator.update_chat(old_rating2, old_rating1)

        return round(max(new_rating2, self.min_rating), 2)

    async def ref(self, rating):
        old_rating = rating.rating_score

        new_rating = await self.calculator.update_ref(old_rating)

        return round(max(new_rating, self.min_rating), 2)