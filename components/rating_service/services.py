class ProfileRatingCalculator:
    BASE_RATING = 800
    MAX_BONUS = 200

    WEIGHTS = {
        'profile_completeness': 0.30,
        'photo_quality': 0.25,
        'description_quality': 0.20,
        'verified': 0.15,
        'social_connections': 0.10
    }

    @classmethod
    def calculate(cls, profile_data):
        """
        Рассчитывает начальный рейтинг на основе данных профиля
        :param profile_data: словарь с данными профиля
        Пример:
        {
            'profile_completeness': 0.85,  # 0-1
            'photo_quality': 0.90,
            'description_quality': 0.75,
            'verified': True,
            'social_connections': 0.60
        }
        """
        score = 0

        # Расчет верифицированного статуса
        verified_score = 1.0 if profile_data.get('verified') else 0.0

        # Суммируем баллы с весами
        score += profile_data.get('profile_completeness', 0) * cls.WEIGHTS['profile_completeness']
        score += profile_data.get('photo_quality', 0) * cls.WEIGHTS['photo_quality']
        score += profile_data.get('description_quality', 0) * cls.WEIGHTS['description_quality']
        score += verified_score * cls.WEIGHTS['verified']
        score += profile_data.get('social_connections', 0) * cls.WEIGHTS['social_connections']

        # Применяем максимальный бонус
        bonus = cls.MAX_BONUS * min(max(score, 0), 1)  # Ограничение 0-1
        return round(cls.BASE_RATING + bonus)


class RatingService:
    def __init__(self, k=32, min_rating=100):
        self.ratings = {}
        self.k = k
        self.min_rating = min_rating

    def init_user(self, user_id, profile_data):
        """Регистрация нового пользователя с расчетом начального рейтинга"""
        initial_rating = ProfileRatingCalculator.calculate(profile_data)
        self.ratings[user_id] = initial_rating
        return initial_rating

    # Остальные методы из предыдущей реализации (get_rating, add_like, add_dislike и т.д.)


class RatingService:
    def __init__(self, initial_rating=1000, k=32, min_rating=100):
        self.ratings = {}
        self.initial_rating = initial_rating
        self.k = k
        self.min_rating = min_rating

    def get_rating(self, user_id):
        return self.ratings.get(user_id, self.initial_rating)

    def _update_rating(self, user_id, delta):
        current = self.get_rating(user_id)
        new_rating = max(current + delta, self.min_rating)
        self.ratings[user_id] = new_rating
        return new_rating

    def _expected_score(self, rating_a, rating_b):
        return 1.0 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def add_like(self, from_user_id, to_user_id):
        r_from = self.get_rating(from_user_id)
        r_to = self.get_rating(to_user_id)

        expected = self._expected_score(r_from, r_to)
        delta = self.k * (1 - expected)
        self._update_rating(to_user_id, delta)

    def add_dislike(self, from_user_id, to_user_id):
        r_from = self.get_rating(from_user_id)
        r_to = self.get_rating(to_user_id)

        expected = self._expected_score(r_from, r_to)
        delta = self.k * (-expected)
        self._update_rating(to_user_id, delta)

    def get_top_users(self, limit=10):
        sorted_users = sorted(self.ratings.items(), key=lambda x: -x[1])
        return sorted_users[:limit]