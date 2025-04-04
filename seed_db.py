import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import text
from app import create_app, db, bcrypt
from app.models.user import User, UserRole, UserEventAchievement, UserOrganizerAchievement
from app.models.event import Event, EventStatus, EventFormat, Tag, EventAchievement, EventReview
from app.models.achievement import Achievement, OrganizerAchievement, AchievementConditionType
from app.models.news import News
from app.models.notification import Notification, NotificationType

app = create_app()

def clear_database():
    """Clear all data from the database"""
    with app.app_context():
        try:
            print("Clearing database...")
            # Disable foreign key checks to allow for easier deletion
            db.session.execute(text("PRAGMA foreign_keys = OFF"))
            
            # Drop all tables
            db.drop_all()
            
            # Re-enable foreign key checks
            db.session.execute(text("PRAGMA foreign_keys = ON"))
            db.session.commit()
            
            print("Database cleared successfully")
        except Exception as e:
            db.session.rollback()
            print(f"Error clearing database: {str(e)}")
            raise

def seed_database():
    """Seed the database with initial data"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        # Create users (admin, organizer, user)
        print("Creating users...")
        admin = User(
            username="admin",
            email="admin@example.ru",
            password=bcrypt.generate_password_hash("admin123").decode('utf-8'),
            role=UserRole.ADMIN.value,
            profile_image="default.jpg",
            created_at=datetime.utcnow()
        )
        
        organizer = User(
            username="organizer",
            email="organizer@example.ru",
            password=bcrypt.generate_password_hash("organizer123").decode('utf-8'),
            role=UserRole.ORGANIZER.value,
            profile_image="default.jpg",
            created_at=datetime.utcnow() - timedelta(days=30)
        )
        
        user = User(
            username="user",
            email="user@example.ru",
            password=bcrypt.generate_password_hash("user123").decode('utf-8'),
            role=UserRole.PARTICIPANT.value,
            profile_image="default.jpg",
            created_at=datetime.utcnow() - timedelta(days=20)
        )
        
        db.session.add_all([admin, organizer, user])
        db.session.commit()
        
        # Create tags
        print("Creating tags...")
        tags = [
            Tag(name="Наука"),
            Tag(name="Технологии"),
            Tag(name="Бизнес"),
            Tag(name="Искусство"),
            Tag(name="Образование"),
            Tag(name="Спорт"),
            Tag(name="Музыка"),
            Tag(name="Культура")
        ]
        db.session.add_all(tags)
        db.session.commit()
        
        # Create news
        print("Creating news articles...")
        news1 = News(
            title="Открытие новой образовательной платформы",
            content="""
            Мы рады сообщить о запуске нашей новой образовательной платформы, предоставляющей широкий спектр курсов и мероприятий.
            
            Платформа предлагает удобный интерфейс для поиска и регистрации на мероприятия, а также систему достижений для мотивации участников и организаторов.
            
            Присоединяйтесь к нам и развивайтесь вместе с нашим сообществом единомышленников!
            """,
            image="default_news.jpg",
            published_at=datetime.utcnow() - timedelta(days=7),
            author_id=admin.id
        )
        
        news2 = News(
            title="Итоги ежегодной технологической конференции",
            content="""
            Подводим итоги ежегодной технологической конференции, которая прошла с большим успехом!
            
            Более 500 участников, 30 докладчиков, 15 мастер-классов и множество полезных контактов. 
            Спасибо всем, кто принял участие и сделал это событие особенным.
            
            Следите за новостями о предстоящих мероприятиях на нашей платформе.
            """,
            image="default_news.jpg",
            published_at=datetime.utcnow() - timedelta(days=3),
            author_id=organizer.id
        )
        
        news3 = News(
            title="Открыт набор в программу менторства для начинающих организаторов",
            content="""
            Запускаем программу менторства для начинающих организаторов мероприятий!
            
            Если вы хотите научиться организовывать качественные события, но не знаете с чего начать, 
            эта программа для вас. Опытные организаторы поделятся своими знаниями и помогут вам развить необходимые навыки.
            
            Для участия необходимо подать заявку до конца месяца. Количество мест ограничено!
            """,
            image="default_news.jpg",
            published_at=datetime.utcnow() - timedelta(days=1),
            author_id=admin.id
        )
        
        db.session.add_all([news1, news2, news3])
        db.session.commit()
        
        # Create events
        print("Creating events...")
        
        # Upcoming events
        now = datetime.utcnow()
        
        event1 = Event(
            title="Мастер-класс по программированию на Python",
            description="""
            Приглашаем на интенсивный мастер-класс по программированию на языке Python для начинающих!
            
            В программе:
            • Основы синтаксиса Python
            • Работа с данными и коллекциями
            • Функции и модули
            • Практические задания с разбором
            
            Мастер-класс проведет опытный разработчик с более чем 5-летним стажем преподавания.
            """,
            start_datetime=now + timedelta(days=14),
            end_datetime=now + timedelta(days=14, hours=3),
            location="Технопарк 'Инновация', ул. Цифровая, 42",
            max_participants=25,
            format=EventFormat.OFFLINE.value,
            status=EventStatus.APPROVED.value,
            organizer_id=organizer.id,
            logo="default_event.jpg",
            created_at=now - timedelta(days=10),
            updated_at=now - timedelta(days=10)
        )
        
        # Add tags to the event
        event1.tags.append(tags[0])  # Наука
        event1.tags.append(tags[1])  # Технологии
        event1.tags.append(tags[4])  # Образование
        
        event2 = Event(
            title="Бизнес-форум 'Стартап Будущего'",
            description="""
            Крупнейший в регионе форум для стартапов и инвесторов!
            
            В программе:
            • Питч-сессии для стартапов
            • Панельные дискуссии с успешными предпринимателями
            • Мастер-классы по привлечению инвестиций
            • Нетворкинг и деловые знакомства
            
            Не упустите шанс найти инвестора для своего проекта или познакомиться с перспективными стартапами!
            """,
            start_datetime=now + timedelta(days=30),
            end_datetime=now + timedelta(days=31),
            location="Бизнес-центр 'Империя', Проспект Предпринимателей, 100",
            max_participants=200,
            format=EventFormat.OFFLINE.value,
            status=EventStatus.APPROVED.value,
            organizer_id=organizer.id,
            logo="default_event.jpg",
            created_at=now - timedelta(days=15),
            updated_at=now - timedelta(days=15)
        )
        
        # Add tags to the event
        event2.tags.append(tags[2])  # Бизнес
        event2.tags.append(tags[1])  # Технологии
        
        event3 = Event(
            title="Онлайн-семинар 'Современное искусство и технологии'",
            description="""
            Приглашаем на онлайн-семинар, посвященный влиянию современных технологий на искусство.

            Темы семинара:
            • Цифровое искусство: прошлое, настоящее и будущее
            • Искусственный интеллект как инструмент художника
            • Виртуальная реальность в современных выставках
            • NFT и цифровые активы в искусстве

            Семинар проведут ведущие эксперты в области искусства и технологий.
            """,
            start_datetime=now + timedelta(days=7),
            end_datetime=now + timedelta(days=7, hours=2),
            location="Онлайн (Zoom)",
            max_participants=100,
            format=EventFormat.ONLINE.value,
            status=EventStatus.APPROVED.value,
            organizer_id=organizer.id,
            logo="default_event.jpg",
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(days=5)
        )
        
        # Add tags to the event
        event3.tags.append(tags[3])  # Искусство
        event3.tags.append(tags[1])  # Технологии
        event3.tags.append(tags[7])  # Культура
        
        # Completed events
        event4 = Event(
            title="Музыкальный фестиваль 'Ритмы Лета'",
            description="""
            Грандиозный музыкальный фестиваль под открытым небом!
            
            В программе:
            • Выступления более 20 музыкальных коллективов
            • Три сцены с разными музыкальными направлениями
            • Фуд-корт с разнообразной кухней
            • Зоны отдыха и развлечений
            
            Проведите незабываемый день в компании единомышленников и любимой музыки!
            """,
            start_datetime=now - timedelta(days=15),
            end_datetime=now - timedelta(days=14),
            location="Городской парк культуры и отдыха",
            max_participants=1000,
            format=EventFormat.OFFLINE.value,
            status=EventStatus.COMPLETED.value,
            organizer_id=organizer.id,
            logo="default_event.jpg",
            created_at=now - timedelta(days=60),
            updated_at=now - timedelta(days=14)
        )
        
        # Add tags to the event
        event4.tags.append(tags[6])  # Музыка
        event4.tags.append(tags[7])  # Культура
        
        event5 = Event(
            title="Спортивный марафон 'Здоровый город'",
            description="""
            Ежегодный городской марафон для любителей бега всех возрастов!
            
            В программе:
            • Дистанции: 5 км, 10 км, 21.1 км (полумарафон)
            • Детский забег на 1 км
            • Медали всем финишерам
            • Спортивный фестиваль и ярмарка
            
            Присоединяйтесь к спортивному празднику и проверьте свои силы!
            """,
            start_datetime=now - timedelta(days=45),
            end_datetime=now - timedelta(days=45, hours=-8),
            location="Центральный стадион и городские улицы",
            max_participants=500,
            format=EventFormat.OFFLINE.value,
            status=EventStatus.COMPLETED.value,
            organizer_id=organizer.id,
            logo="default_event.jpg",
            created_at=now - timedelta(days=90),
            updated_at=now - timedelta(days=45)
        )
        
        # Add tags to the event
        event5.tags.append(tags[5])  # Спорт
        
        db.session.add_all([event1, event2, event3, event4, event5])
        db.session.commit()
        
        # Create achievements for participants
        print("Creating participant achievements...")
        
        achievement1 = Achievement(
            name="Новичок",
            description="Зарегистрировался на первое мероприятие",
            icon="default_achievement.png",
            points=10,
            condition="first_event_registration"
        )
        
        achievement2 = Achievement(
            name="Активный участник",
            description="Зарегистрировался на 5 мероприятий",
            icon="achievement_participation.png",
            points=50,
            condition="five_events_registration"
        )
        
        achievement3 = Achievement(
            name="Эксперт",
            description="Посетил более 10 мероприятий",
            icon="achievement_participation.png",
            points=100,
            condition="ten_events_visited"
        )
        
        db.session.add_all([achievement1, achievement2, achievement3])
        db.session.commit()
        
        # Create achievements for organizers
        print("Creating organizer achievements...")
        
        org_achievement1 = OrganizerAchievement(
            name="Начинающий организатор",
            description="Успешно провел первое мероприятие",
            icon="achievement_organizer.png",
            condition_type=AchievementConditionType.EVENTS_COUNT.value,
            condition_value=1,
            points=20
        )
        
        org_achievement2 = OrganizerAchievement(
            name="Опытный организатор",
            description="Успешно провел 5 мероприятий",
            icon="achievement_organizer.png",
            condition_type=AchievementConditionType.EVENTS_COUNT.value,
            condition_value=5,
            points=100
        )
        
        org_achievement3 = OrganizerAchievement(
            name="Популярный организатор",
            description="Собрал более 100 участников на своих мероприятиях",
            icon="achievement_organizer.png",
            condition_type=AchievementConditionType.PARTICIPANTS_COUNT.value,
            condition_value=100,
            points=50
        )
        
        db.session.add_all([org_achievement1, org_achievement2, org_achievement3])
        db.session.commit()
        
        # Create achievements for specific events
        print("Creating event achievements...")
        
        event_achievement1 = EventAchievement(
            name="Марафонец",
            description="Успешно пробежал полумарафон",
            points=30,
            icon="achievement_special.png",
            event_id=event5.id
        )
        
        event_achievement2 = EventAchievement(
            name="Музыкальный фанат",
            description="Посетил все три сцены фестиваля",
            points=20,
            icon="achievement_special.png",
            event_id=event4.id
        )
        
        db.session.add_all([event_achievement1, event_achievement2])
        db.session.commit()
        
        # Assign achievements to users
        print("Assigning achievements to users...")
        
        # Assign participant achievements to user
        user.achievements.append(achievement1)  # Новичок
        
        # Assign event achievements to user
        user_event_achievement1 = UserEventAchievement(
            user_id=user.id,
            achievement_id=event_achievement1.id,
            event_id=event5.id,
            date_earned=datetime.utcnow() - timedelta(days=43)
        )
        
        # Assign organizer achievements to organizer
        user_org_achievement1 = UserOrganizerAchievement(
            user_id=organizer.id,
            achievement_id=org_achievement1.id,
            date_earned=datetime.utcnow() - timedelta(days=44)
        )
        
        user_org_achievement2 = UserOrganizerAchievement(
            user_id=organizer.id,
            achievement_id=org_achievement3.id,
            date_earned=datetime.utcnow() - timedelta(days=14)
        )
        
        db.session.add_all([user_event_achievement1, user_org_achievement1, user_org_achievement2])
        db.session.commit()
        
        # Create reviews for completed events
        print("Creating event reviews...")
        
        review1 = EventReview(
            event_id=event4.id,
            user_id=user.id,
            rating=5,
            comment="Отличный музыкальный фестиваль! Все было организовано на высшем уровне. Обязательно приду в следующем году!",
            created_at=datetime.utcnow() - timedelta(days=14)
        )
        
        review2 = EventReview(
            event_id=event5.id,
            user_id=user.id,
            rating=4,
            comment="Хороший марафон, но были некоторые проблемы с организацией пунктов питания. В целом понравилось, буду участвовать снова.",
            created_at=datetime.utcnow() - timedelta(days=42)
        )
        
        db.session.add_all([review1, review2])
        db.session.commit()
        
        # Create notifications
        print("Creating notifications...")
        
        notification1 = Notification(
            user_id=user.id,
            type=NotificationType.ACHIEVEMENT_EARNED.value,
            content="Вы получили достижение 'Новичок'",
            is_read=False,
            created_at=datetime.utcnow() - timedelta(days=19),
            related_id=achievement1.id
        )
        
        notification2 = Notification(
            user_id=user.id,
            type=NotificationType.ACHIEVEMENT_EARNED.value,
            content="Вы получили достижение 'Марафонец' за участие в марафоне 'Здоровый город'",
            is_read=False,
            created_at=datetime.utcnow() - timedelta(days=43),
            related_id=event_achievement1.id
        )
        
        notification3 = Notification(
            user_id=organizer.id,
            type=NotificationType.ACHIEVEMENT_EARNED.value,
            content="Вы получили достижение 'Начинающий организатор'",
            is_read=False,
            created_at=datetime.utcnow() - timedelta(days=44),
            related_id=org_achievement1.id
        )
        
        notification4 = Notification(
            user_id=organizer.id,
            type=NotificationType.ACHIEVEMENT_EARNED.value,
            content="Вы получили достижение 'Популярный организатор'",
            is_read=False,
            created_at=datetime.utcnow() - timedelta(days=14),
            related_id=org_achievement3.id
        )
        
        db.session.add_all([notification1, notification2, notification3, notification4])
        db.session.commit()
        
        print("Database seeding completed successfully!")

if __name__ == "__main__":
    try:
        clear_database()
        seed_database()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1) 