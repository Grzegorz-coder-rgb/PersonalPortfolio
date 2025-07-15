# your_project/main.py (CAŁA ZAWARTOŚĆ PLIKU)

from flask import Flask, render_template, url_for, request, redirect, flash, session, jsonify # Importuje niezbędne klasy i funkcje z biblioteki Flask.
# Flask: Główna klasa aplikacji Flask.
# render_template: Funkcja do renderowania szablonów HTML.
# url_for: Funkcja do generowania URL-i dla funkcji widoków.
# request: Obiekt zawierający dane z bieżącego żądania HTTP (np. dane formularza).
# redirect: Funkcja do przekierowywania użytkownika na inny URL.
# flash: Funkcja do wyświetlania jednorazowych komunikatów użytkownikowi (np. "Zalogowano pomyślnie!").
# session: Obiekt do zarządzania sesjami użytkowników (przechowywanie danych specyficznych dla użytkownika między żądaniami).
# jsonify: Funkcja do konwertowania danych Pythona na odpowiedź JSON.

from models import db, User, Course, Module, Lesson, UserCourseAccess # Importuje instancję bazy danych (db) oraz wszystkie zdefiniowane modele ORM (Object-Relational Mapping) z pliku `models.py`.
# db: Instancja SQLAlchemy do interakcji z bazą danych.
# User, Course, Module, Lesson, UserCourseAccess: Klasy reprezentujące tabele w bazie danych.

from werkzeug.security import generate_password_hash, check_password_hash # Importuje funkcje do bezpiecznego hashowania i weryfikowania haseł.
# generate_password_hash: Tworzy bezpieczny hash hasła.
# check_password_hash: Sprawdza, czy podane hasło pasuje do hashu.

from functools import wraps # Importuje `wraps` z modułu `functools`, używane do tworzenia dekoratorów.

import os # Importuje moduł `os`, który zapewnia sposób interakcji z systemem operacyjnym (np. dostęp do zmiennych środowiskowych, ścieżek plików).

# --- WAŻNE: Dodajemy bibliotekę dotenv do ładowania zmiennych środowiskowych lokalnie ---
# Komentarz informujący o celu użycia `python-dotenv`.
# W środowisku produkcyjnym (np. na Render.com) to nie będzie potrzebne, bo Render sam wczyta zmienne.
# Komentarz wyjaśniający, że na produkcji zmienne są ładowane automatycznie.
# Ale lokalnie pomoże to ukryć wrażliwe dane.
# Komentarz podkreślający korzyści lokalnego użycia.
# Pamiętaj, że musisz ją zainstalować: pipenv install python-dotenv
# Komentarz z instrukcją instalacji.
try: # Rozpoczyna blok `try` do obsługi potencjalnego błędu importu.
    from dotenv import load_dotenv # Próbuje zaimportować funkcję `load_dotenv` z biblioteki `dotenv`.
    load_dotenv() # Wywołuje `load_dotenv()`, aby załadować zmienne środowiskowe z pliku `.env` (jeśli istnieje) do pamięci.
except ImportError: # Jeśli import `dotenv` się nie powiedzie (np. biblioteka nie jest zainstalowana).
    # Ignoruj, jeśli dotenv nie jest zainstalowane (np. na produkcji lub w środowisku bez pliku .env)
    pass # Ignoruje błąd, co pozwala aplikacji działać nawet bez `dotenv`.


app = Flask(__name__) # Tworzy instancję aplikacji Flask. `__name__` to nazwa bieżącego modułu, która pomaga Flaskowi znaleźć zasoby.

# --- KONFIGURACJA APLIKACJI ---

# 1. Konfiguracja bazy danych
# Komentarz wyjaśniający sekcję konfiguracji bazy danych.
# Lokalnie używamy SQLite, ale na produkcji (Render) użyjemy PostgreSQL.
# Komentarz o wyborze baz danych w zależności od środowiska.
# Render udostępnia URL do bazy danych w zmiennej środowiskowej 'DATABASE_URL'.
# Komentarz o zmiennej środowiskowej na Render.com.
# Używamy os.environ.get(), aby dynamicznie pobierać ten URL.
# Komentarz o dynamicznym pobieraniu URL-a.
# Jeśli 'DATABASE_URL' nie jest ustawione (czyli lokalnie), używamy domyślnej ścieżki do SQLite.
# Komentarz o domyślnej ścieżce dla SQLite.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get( # Ustawia URI bazy danych dla SQLAlchemy.
    'DATABASE_URL', # Próbuje pobrać wartość zmiennej środowiskowej 'DATABASE_URL'.
    'sqlite:///' + os.path.join(app.instance_path, 'site.db') # Jeśli 'DATABASE_URL' nie jest ustawione, używa ścieżki do pliku SQLite w folderze `instance`.
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Wyłącza śledzenie modyfikacji obiektów SQLAlchemy, co zużywa mniej pamięci i jest zalecane.

# 2. Sekretny klucz dla Flask
# Komentarz wyjaśniający sekcję sekretnego klucza.
# BARDZO WAŻNE: Na produkcji (Render) ustaw 'SECRET_KEY' jako zmienną środowiskową!
# Komentarz podkreślający ważność ustawienia klucza na produkcji.
# Ta domyślna wartość jest tylko dla developmentu. Używamy os.urandom(24).hex()
# Komentarz o domyślnej wartości dla developmentu.
# do generowania losowego, bezpiecznego klucza programistycznie, jeśli zmienna nie jest ustawiona.
# Komentarz o generowaniu klucza.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex()) # Ustawia sekretny klucz aplikacji Flask, używany do podpisywania ciasteczek sesji i innych celów bezpieczeństwa. Generuje losowy klucz, jeśli zmienna środowiskowa 'SECRET_KEY' nie jest ustawiona.

# Utwórz folder 'instance' jeśli nie istnieje (potrzebne dla SQLite w app.instance_path)
# Komentarz o tworzeniu folderu `instance`.
if not os.path.exists(app.instance_path): # Sprawdza, czy folder `instance` (domyślna lokalizacja dla plików aplikacji) nie istnieje.
    os.makedirs(app.instance_path) # Tworzy folder `instance`, jeśli nie istnieje. Jest to potrzebne dla bazy danych SQLite.

# === WAŻNE: Zainicjuj 'db' z 'app' TYLKO RAZ i PRZED Użyciem Modeli SQLAlchemy ===
# Komentarz podkreślający jednokrotną inicjalizację `db`.
db.init_app(app) # Inicjalizuje instancję SQLAlchemy (`db`) z aplikacją Flask (`app`). To łączy bazę danych z aplikacją.

# === Funkcja do inicjalizacji bazy danych i dodawania przykładowych danych ===
# Komentarz wyjaśniający cel funkcji.
def init_db_and_data(): # Definiuje funkcję `init_db_and_data` do inicjalizacji bazy danych i wypełniania jej początkowymi danymi.
    with app.app_context(): # Wchodzi w kontekst aplikacji Flask. Jest to konieczne do wykonywania operacji na bazie danych poza widokami.
        db.create_all() # Tworzy wszystkie tabele w bazie danych, bazując na zdefiniowanych modelach SQLAlchemy, jeśli jeszcze nie istnieją.

        if not User.query.first(): # Sprawdza, czy w tabeli `User` nie ma żadnych rekordów. `User.query.first()` zwraca pierwszego użytkownika lub `None`.
            print("Dodawanie przykładowych danych...") # Wyświetla komunikat informujący o dodawaniu danych.

            # --- WAŻNE: POBIERANIE HASŁA I EMAILA ADMINA ZE ZMIENNYCH ŚRODOWISKOWYCH ---
            # Komentarz o pobieraniu danych admina.
            # To są zmienne, które ustawisz w pliku .env lokalnie
            # Komentarz o pliku `.env`.
            # i na Render.com w sekcji Environment Variables.
            # Komentarz o Render.com.
            admin_email = os.environ.get('ADMIN_EMAIL') # Pobiera adres e-mail administratora ze zmiennych środowiskowych.
            admin_password = os.environ.get('ADMIN_PASSWORD') # Pobiera hasło administratora ze zmiennych środowiskowych.

            # Sprawdź, czy zmienne środowiskowe dla admina zostały ustawione
            # Komentarz o sprawdzaniu zmiennych admina.
            if not admin_email or not admin_password: # Sprawdza, czy zmienne `admin_email` lub `admin_password` nie są puste.
                print("--- BŁĄD: Nie ustawiono ADMIN_EMAIL lub ADMIN_PASSWORD w zmiennych środowiskowych! ---") # Wyświetla komunikat o błędzie, jeśli zmienne nie są ustawione.
                print("Nie dodano użytkownika admina. Ustaw je w .env (lokalnie) i na Render.com.") # Instrukcja dla użytkownika.
                # Nie zwracamy, aby reszta danych kursów mogła się dodać, jeśli to tylko problem z adminem.
                # Komentarz wyjaśniający, dlaczego funkcja nie kończy działania.
                # Ale admin nie zostanie dodany.
                # Komentarz potwierdzający, że admin nie zostanie dodany.
            else: # Jeśli zmienne środowiskowe dla admina są ustawione.
                admin_user = User(username='admin', email=admin_email, lessons_balance=100, role='admin') # Tworzy nowy obiekt `User` dla administratora z domyślnymi wartościami.
                admin_user.password_hash = generate_password_hash(admin_password) # Haszuje hasło administratora i przypisuje je do atrybutu `password_hash` obiektu `admin_user`.
                db.session.add(admin_user) # Dodaje obiekt `admin_user` do sesji bazy danych.
                db.session.commit() # Zatwierdza zmiany w bazie danych, co powoduje zapisanie użytkownika admina i przypisanie mu ID.
                # Automatyczne przypisanie kursu do admina
                # Komentarz o automatycznym przypisaniu kursu.
                # Ten blok kodu był wcześniej niekompletny i potencjalnie błędny. Usunięto go, ponieważ przypisanie kursów do admina następuje później.
                # if 'user_id' in session:
                #     admin_id = session['user_id']
                #     new_access = UserCourseAccess(
                #         user_id=admin_id,
                #         course_id=new_course.id,
                #         lessons_completed=0,
                #         current_lesson_id=None
                #     )
                #     db.session.add(new_access)
                #     db.session.commit()



                # --- Reszta kodu do dodawania danych kursów pozostaje bez zmian ---
                # Komentarz informujący, że poniżej znajduje się kod do dodawania danych kursów.
                courses_data = [ # Definiuje listę słowników `courses_data`, gdzie każdy słownik reprezentuje dane dla jednego kursu.
                    { # Początek definicji pierwszego kursu (Python Dev).
                        'name': 'Python Dev', # Nazwa kursu.
                        'description': 'Kompleksowy kurs programowania w Pythonie od podstaw.', # Opis kursu.
                        'gradient_class': 'course-gradient-python', # Klasa CSS do stylizacji gradientu kursu.
                        'modules': [ # Lista słowników, gdzie każdy słownik reprezentuje moduł w tym kursie.
                            {'name': 'Moduł 1: Podstawy Pythona', 'gradient_class': 'module-gradient-1', 'lessons_count': 4}, # Dane dla Modułu 1.
                            {'name': 'Moduł 2: Struktury Danych', 'gradient_class': 'module-gradient-2', 'lessons_count': 4}, # Dane dla Modułu 2.
                            {'name': 'Moduł 3: Funkcje i Moduły', 'gradient_class': 'module-gradient-3', 'lessons_count': 4}, # Dane dla Modułu 3.
                            {'name': 'Moduł 4: Programowanie Obiektowe', 'gradient_class': 'module-gradient-4', 'lessons_count': 4}, # Dane dla Modułu 4.
                            {'name': 'Moduł 5: Obsługa Plików i Wyjątków', 'gradient_class': 'module-gradient-5', 'lessons_count': 4}, # Dane dla Modułu 5.
                            {'name': 'Moduł 6: Web Scraping i API', 'gradient_class': 'module-gradient-6', 'lessons_count': 4}, # Dane dla Modułu 6.
                            {'name': 'Moduł 7: Bazy Danych z Pythonem', 'gradient_class': 'module-gradient-7', 'lessons_count': 4}, # Dane dla Modułu 7.
                            {'name': 'Moduł 8: Wprowadzenie do Flask', 'gradient_class': 'module-gradient-8', 'lessons_count': 4} # Dane dla Modułu 8.
                        ]
                    }, # Koniec definicji pierwszego kursu.
                    { # Początek definicji drugiego kursu (Full Stack).
                        'name': 'Full Stack', # Nazwa kursu.
                        'description': 'Kompleksowy kurs tworzenia pełnych aplikacji webowych.', # Opis kursu.
                        'gradient_class': 'course-gradient-fullstack', # Klasa CSS do stylizacji gradientu kursu.
                        'modules': [ # Lista słowników, gdzie każdy słownik reprezentuje moduł w tym kursie.
                            {'name': 'FS Moduł 1: Wprowadzenie do Frontend', 'gradient_class': 'module-gradient-fullstack-1', 'lessons_count': 4}, # Dane dla Modułu 1.
                            {'name': 'FS Moduł 2: CSS Zaawansowany', 'gradient_class': 'module-gradient-fullstack-2', 'lessons_count': 4}, # Dane dla Modułu 2.
                            {'name': 'FS Moduł 3: JavaScript ES6+', 'gradient_class': 'module-gradient-fullstack-3', 'lessons_count': 4}, # Dane dla Modułu 3.
                            {'name': 'FS Moduł 4: React.js Podstawy', 'gradient_class': 'module-gradient-fullstack-4', 'lessons_count': 4}, # Dane dla Modułu 4.
                            {'name': 'FS Moduł 5: Node.js i Express', 'gradient_class': 'module-gradient-fullstack-5', 'lessons_count': 4}, # Dane dla Modułu 5.
                            {'name': 'FS Moduł 6: Bazy Danych NoSQL', 'gradient_class': 'module-gradient-fullstack-6', 'lessons_count': 4}, # Dane dla Modułu 6.
                            {'name': 'FS Moduł 7: RESTful API', 'gradient_class': 'module-gradient-fullstack-7', 'lessons_count': 4}, # Dane dla Modułu 7.
                            {'name': 'FS Moduł 8: Deployment i CI/CD', 'gradient_class': 'module-gradient-fullstack-8', 'lessons_count': 4} # Dane dla Modułu 8.
                        ]
                    }, # Koniec definicji drugiego kursu.
                    { # Początek definicji trzeciego kursu (AI & ML Dev).
                        'name': 'AI & ML Dev', # Nazwa kursu.
                        'description': 'Kurs wprowadzający do sztucznej inteligencji i uczenia maszynowego.', # Opis kursu.
                        'gradient_class': 'course-gradient-aiml', # Klasa CSS do stylizacji gradientu kursu.
                        'modules': [ # Lista słowników, gdzie każdy słownik reprezentuje moduł w tym kursie.
                            {'name': 'AI/ML Moduł 1: Wprowadzenie do AI/ML', 'gradient_class': 'module-gradient-aiml-1', 'lessons_count': 4}, # Dane dla Modułu 1.
                            {'name': 'AI/ML Moduł 2: Podstawy Pythona dla ML', 'gradient_class': 'module-gradient-aiml-2', 'lessons_count': 4}, # Dane dla Modułu 2.
                            {'name': 'AI/ML Moduł 3: Statystyka i Prawdopodobieństwo', 'gradient_class': 'module-gradient-aiml-3', 'lessons_count': 4}, # Dane dla Modułu 3.
                            {'name': 'AI/ML Moduł 4: Uczenie Nadzorowane', 'gradient_class': 'module-gradient-aiml-4', 'lessons_count': 4}, # Dane dla Modułu 4.
                            {'name': 'AI/ML Moduł 5: Uczenie Nienadzorowane', 'gradient_class': 'module-gradient-aiml-5', 'lessons_count': 4}, # Dane dla Modułu 5.
                            {'name': 'AI/ML Moduł 6: Sieci Neuronowe i Deep Learning', 'gradient_class': 'module-gradient-aiml-6', 'lessons_count': 4}, # Dane dla Modułu 6.
                            {'name': 'AI/ML Moduł 7: Przetwarzanie Języka Naturalnego (NLP)', 'gradient_class': 'module-gradient-aiml-7', 'lessons_count': 4}, # Dane dla Modułu 7.
                            {'name': 'AI/ML Moduł 8: Wizja Komputerowa', 'gradient_class': 'module-gradient-aiml-8', 'lessons_count': 4} # Dane dla Modułu 8.
                        ]
                    }, # Koniec definicji trzeciego kursu.
                    { # Początek definicji czwartego kursu (Frontend Dev).
                        'name': 'Frontend Dev', # Nazwa kursu.
                        'description': 'Kurs skupiający się na tworzeniu interfejsów użytkownika.', # Opis kursu.
                        'gradient_class': 'course-gradient-frontend', # Klasa CSS do stylizacji gradientu kursu.
                        'modules': [ # Lista słowników, gdzie każdy słownik reprezentuje moduł w tym kursie.
                            {'name': 'FE Moduł 1: HTML5 i CSS3', 'gradient_class': 'module-gradient-frontend-1', 'lessons_count': 4}, # Dane dla Modułu 1.
                            {'name': 'FE Moduł 2: Responsywny Design', 'gradient_class': 'module-gradient-frontend-2', 'lessons_count': 4}, # Dane dla Modułu 2.
                            {'name': 'FE Moduł 3: Zaawansowany CSS i Animacje', 'gradient_class': 'module-gradient-frontend-3', 'lessons_count': 4}, # Dane dla Modułu 3.
                            {'name': 'FE Moduł 4: JavaScript od Podstaw', 'gradient_class': 'module-gradient-frontend-4', 'lessons_count': 4}, # Dane dla Modułu 4.
                            {'name': 'FE Moduł 5: DOM Manipulation', 'gradient_class': 'module-gradient-frontend-5', 'lessons_count': 4}, # Dane dla Modułu 5.
                            {'name': 'FE Moduł 6: Asynchroniczny JavaScript', 'gradient_class': 'module-gradient-frontend-6', 'lessons_count': 4}, # Dane dla Modułu 6.
                            {'name': 'FE Moduł 7: React Podstawy', 'gradient_class': 'module-gradient-frontend-7', 'lessons_count': 4}, # Dane dla Modułu 7.
                            {'name': 'FE Moduł 8: Narzędzia Frontendowe', 'gradient_class': 'module-gradient-frontend-8', 'lessons_count': 4} # Dane dla Modułu 8.
                        ]
                    }, # Koniec definicji czwartego kursu.
                ] # Koniec listy `courses_data`.

                all_courses_in_db = [] # Inicjalizuje pustą listę do przechowywania obiektów kursów po ich dodaniu do bazy danych.
                for c_data in courses_data: # Rozpoczyna pętlę iterującą przez każdy słownik kursu w liście `courses_data`.
                    total_lessons_in_course = sum(m['lessons_count'] for m in c_data['modules']) # Oblicza całkowitą liczbę lekcji w bieżącym kursie, sumując `lessons_count` z każdego modułu.
                    course = Course( # Tworzy nowy obiekt `Course` (model ORM).
                        name=c_data['name'], # Ustawia nazwę kursu z danych.
                        description=c_data['description'], # Ustawia opis kursu z danych.
                        gradient_class=c_data['gradient_class'], # Ustawia klasę gradientu z danych.
                        total_lessons=total_lessons_in_course # Ustawia całkowitą liczbę lekcji dla kursu.
                    )
                    db.session.add(course) # Dodaje nowo utworzony obiekt `course` do sesji bazy danych.
                    db.session.commit() # Zatwierdza zmiany w bazie danych, co powoduje zapisanie kursu i przypisanie mu unikalnego ID.
                    all_courses_in_db.append(course) # Dodaje obiekt `course` do listy `all_courses_in_db`.

                    for i, m_data in enumerate(c_data['modules']): # Rozpoczyna zagnieżdżoną pętlę iterującą przez moduły bieżącego kursu, z `i` jako indeksem i `m_data` jako danymi modułu.
                        module = Module( # Tworzy nowy obiekt `Module` (model ORM).
                            course_id=course.id, # Przypisuje ID kursu, do którego należy ten moduł.
                            name=m_data['name'], # Ustawia nazwę modułu z danych.
                            order=i + 1, # Ustawia kolejność modułu (indeks + 1, aby zaczynać od 1).
                            total_lessons=m_data['lessons_count'], # Ustawia całkowitą liczbę lekcji dla modułu.
                            gradient_class=m_data['gradient_class'] # Ustawia klasę gradientu modułu.
                        )
                        db.session.add(module) # Dodaje nowo utworzony obiekt `module` do sesji bazy danych.
                        db.session.commit() # Zatwierdza zmiany w bazie danych, co powoduje zapisanie modułu i przypisanie mu unikalnego ID.

                        # Dodaj lekcje do każdego modułu
                        # Komentarz informujący o dodawaniu lekcji.
                        for j in range(1, m_data['lessons_count'] + 1): # Rozpoczyna kolejną zagnieżdżoną pętlę, iterującą od 1 do liczby lekcji w bieżącym module.
                            lesson = Lesson( # Tworzy nowy obiekt `Lesson` (model ORM).
                                module_id=module.id, # Przypisuje ID modułu, do którego należy ta lekcja.
                                name=f'Lekcja {module.order}.{j}: Temat Lekcji {j}', # Generuje nazwę lekcji na podstawie numeru modułu i lekcji.
                                content=f'To jest treść lekcji {module.order}.{j} dla modułu "{module.name}" w kursie "{course.name}".', # Generuje przykładową treść lekcji.
                                order=j # Ustawia kolejność lekcji w module.
                            )
                            db.session.add(lesson) # Dodaje nowo utworzony obiekt `lesson` do sesji bazy danych.
                db.session.commit() # Zatwierdza wszystkie lekcje i moduły na raz (po zakończeniu wszystkich pętli wewnętrznych dla danego kursu).

                # Przypisz wszystkie kursy do użytkownika admina
                # Komentarz o przypisywaniu kursów do admina.
                for course_obj in all_courses_in_db: # Rozpoczyna pętlę iterującą przez wszystkie obiekty kursów, które zostały dodane do bazy danych.
                    user_course_access = UserCourseAccess(user_id=admin_user.id, course_id=course_obj.id, lessons_completed=0) # Tworzy nowy obiekt `UserCourseAccess`, łączący użytkownika admina z bieżącym kursem.
                    db.session.add(user_course_access) # Dodaje nowo utworzony obiekt `user_course_access` do sesji bazy danych.
                db.session.commit() # Zatwierdza wszystkie zmiany w bazie danych, zapisując wszystkie przypisania kursów do admina.
                print("Przykładowe dane dodane.") # Wyświetla komunikat potwierdzający dodanie przykładowych danych.
        else: # Jeśli `User.query.first()` zwróciło użytkownika (czyli baza danych nie jest pusta).
            print("Baza danych już zawiera dane. Jeśli chcesz ją zresetować, usuń plik 'site.db' w folderze 'instance'.") # Wyświetla komunikat informujący, że baza danych już zawiera dane i jak ją zresetować.


# === Funkcje pomocnicze (Dekoratory) ===
# Komentarz wprowadzający sekcję funkcji pomocniczych (dekoratorów).

def is_logged_in(f): # Definiuje dekorator `is_logged_in`, który przyjmuje funkcję `f` jako argument.
    @wraps(f) # Używa `wraps` do zachowania metadanych oryginalnej funkcji `f` (np. nazwy, docstringa).
    def wrap(*args, **kwargs): # Definiuje funkcję wewnętrzną `wrap`, która będzie faktycznie wywoływana. Przyjmuje dowolne argumenty.
        if 'logged_in' in session and session['logged_in']: # Sprawdza, czy klucz 'logged_in' istnieje w sesji i czy jego wartość jest prawdziwa (użytkownik jest zalogowany).
            return f(*args, **kwargs) # Jeśli użytkownik jest zalogowany, wywołuje oryginalną funkcję `f` z jej argumentami.
        else: # Jeśli użytkownik nie jest zalogowany.
            flash('Musisz się zalogować, aby uzyskać dostęp do tej strony.', 'danger') # Wyświetla komunikat flash o błędzie logowania.
            return redirect(url_for('login')) # Przekierowuje użytkownika na stronę logowania.
    return wrap # Zwraca funkcję `wrap`, która zastąpi oryginalną funkcję.

def admin_required(f): # Definiuje dekorator `admin_required`, który przyjmuje funkcję `f` jako argument.
    @wraps(f) # Używa `wraps` do zachowania metadanych oryginalnej funkcji `f`.
    def wrap(*args, **kwargs): # Definiuje funkcję wewnętrzną `wrap`.
        if 'logged_in' in session and session['logged_in'] and session.get('user_role') == 'admin': # Sprawdza, czy użytkownik jest zalogowany ORAZ czy jego rola w sesji to 'admin'.
            return f(*args, **kwargs) # Jeśli użytkownik jest adminem i zalogowany, wywołuje oryginalną funkcję `f`.
        else: # Jeśli użytkownik nie jest adminem lub nie jest zalogowany.
            flash('Brak uprawnień. Tylko administratorzy mogą uzyskać dostęp do tej strony.', 'danger') # Wyświetla komunikat flash o braku uprawnień.
            return redirect(url_for('index')) # Przekierowuje użytkownika na stronę główną.
    return wrap # Zwraca funkcję `wrap`.

# === Flask Routes ===
# Komentarz wprowadzający sekcję tras (widoków) Flask.

# Strona główna (Twoje portfolio)
# Komentarz opisujący trasę strony głównej.
@app.route('/') # Dekorator Flask, który mapuje URL '/' do funkcji `index`.
def index(): # Definiuje funkcję widoku `index`, która obsługuje żądania dla strony głównej.
    login_url = url_for('login') # Generuje URL dla funkcji `login`.
    learn_url = url_for('learn') if 'user_id' in session else url_for('login') # Generuje URL dla strony nauki, jeśli użytkownik jest zalogowany, w przeciwnym razie dla strony logowania.
    return render_template('index.html', login_url=login_url, learn_url=learn_url) # Renderuje szablon `index.html` i przekazuje do niego zmienne `login_url` i `learn_url`.

# Logowanie
# Komentarz opisujący trasę logowania.
@app.route('/login', methods=['GET', 'POST']) # Dekorator Flask, który mapuje URL '/login' do funkcji `login`. Akceptuje metody GET i POST.
def login(): # Definiuje funkcję widoku `login`.
    if 'user_id' in session: # Sprawdza, czy `user_id` jest już w sesji (użytkownik jest już zalogowany).
        return redirect(url_for('learn')) # Jeśli tak, przekierowuje użytkownika bezpośrednio do strony nauki.

    if request.method == 'POST': # Sprawdza, czy żądanie HTTP jest typu POST (czyli formularz został wysłany).
        username = request.form['username'] # Pobiera nazwę użytkownika z danych formularza.
        password = request.form['password'] # Pobiera hasło z danych formularza.

        user = User.query.filter_by(username=username).first() # Szuka użytkownika w bazie danych po nazwie użytkownika.
        if user and check_password_hash(user.password_hash, password): # Sprawdza, czy użytkownik istnieje i czy podane hasło pasuje do zahashowanego hasła w bazie danych.
            session['logged_in'] = True # Ustawia flagę `logged_in` w sesji na True.
            session['username'] = user.username # Zapisuje nazwę użytkownika w sesji.
            session['user_id'] = user.id # Zapisuje ID użytkownika w sesji.
            session['user_role'] = user.role # Zapisuje rolę użytkownika w sesji.
            flash('Zalogowano pomyślnie!', 'success') # Wyświetla komunikat flash o sukcesie logowania.
            return redirect(url_for('learn')) # Przekierowuje użytkownika na stronę nauki.
        else: # Jeśli użytkownik nie istnieje lub hasło jest nieprawidłowe.
            flash('Nieprawidłowa nazwa użytkownika lub hasło.', 'error') # Wyświetla komunikat flash o błędzie logowania.
    return render_template('login.html') # Renderuje szablon `login.html` (dla żądań GET lub nieudanych POST).

# Wylogowanie
# Komentarz opisujący trasę wylogowania.
@app.route('/logout') # Dekorator Flask, który mapuje URL '/logout' do funkcji `logout`.
def logout(): # Definiuje funkcję widoku `logout`.
    session.pop('user_id', None) # Usuwa klucz 'user_id' z sesji. `None` jako drugi argument zapobiega błędowi, jeśli klucz nie istnieje.
    session.pop('username', None) # Usuwa klucz 'username' z sesji.
    session.pop('user_role', None) # Usuwa klucz 'user_role' z sesji.
    session.pop('logged_in', None) # Usuwa klucz 'logged_in' z sesji.
    flash('Zostałeś wylogowany.', 'info') # Wyświetla komunikat flash o wylogowaniu.
    return redirect(url_for('login')) # Przekierowuje użytkownika na stronę logowania.

# Panel nauki (learn.html)
# Komentarz opisujący trasę panelu nauki.
@app.route('/learn') # Dekorator Flask, który mapuje URL '/learn' do funkcji `learn`.
@is_logged_in # Dekorator `is_logged_in` upewnia się, że tylko zalogowani użytkownicy mają dostęp do tej trasy.
def learn(): # Definiuje funkcję widoku `learn`.
    user_id = session['user_id'] # Pobiera ID zalogowanego użytkownika z sesji.
    current_user = User.query.get(user_id) # Pobiera obiekt użytkownika z bazy danych na podstawie jego ID.

    if not current_user: # Sprawdza, czy użytkownik został znaleziony w bazie danych.
        flash('Użytkownik nie znaleziony.', 'error') # Wyświetla komunikat o błędzie.
        return redirect(url_for('logout')) # Przekierowuje do wylogowania, jeśli użytkownik nie istnieje.

    user_courses_data = [] # Inicjalizuje pustą listę do przechowywania danych o kursach użytkownika.
    user_courses_relationships = UserCourseAccess.query.filter_by(user_id=user_id).all() # Pobiera wszystkie rekordy `UserCourseAccess` dla bieżącego użytkownika.

    for uc_rel in user_courses_relationships: # Iteruje przez każdy rekord dostępu użytkownika do kursu.
        course = Course.query.get(uc_rel.course_id) # Pobiera obiekt kursu powiązany z bieżącym rekordem dostępu.
        if course: # Sprawdza, czy kurs istnieje.
            modules_data = [] # Inicjalizuje pustą listę do przechowywania danych o modułach dla bieżącego kursu.
            course_global_lessons_count = 0 # Inicjalizuje licznik globalnych lekcji w kursie.
            for module in sorted(course.modules, key=lambda m: m.order): # Iteruje przez moduły kursu, posortowane według kolejności.
                lessons_in_module = Lesson.query.filter_by(module_id=module.id).count() # Liczy lekcje w bieżącym module.

                module_start_global_index = course_global_lessons_count # Oblicza globalny indeks początkowy dla bieżącego modułu.
                lessons_completed_in_module = max(0, min(lessons_in_module, uc_rel.lessons_completed - module_start_global_index)) # Oblicza liczbę ukończonych lekcji w bieżącym module, uwzględniając postęp użytkownika w całym kursie.

                module_status = "not_started" # Domyślny status modułu.
                if lessons_in_module > 0 and lessons_completed_in_module == lessons_in_module: # Jeśli wszystkie lekcje w module zostały ukończone.
                    module_status = "completed" # Ustawia status na "completed".
                elif lessons_completed_in_module > 0 and lessons_completed_in_module < lessons_in_module: # Jeśli niektóre lekcje zostały ukończone, ale nie wszystkie.
                    module_status = "in_progress" # Ustawia status na "in_progress".

                lessons_for_module = Lesson.query.filter_by(module_id=module.id).order_by(Lesson.order).all() # Pobiera wszystkie lekcje dla bieżącego modułu, posortowane według kolejności.
                module_lessons_list = [] # Inicjalizuje pustą listę do przechowywania szczegółów lekcji.
                for lesson in lessons_for_module: # Iteruje przez lekcje w module.
                    module_lessons_list.append({ # Dodaje słownik z danymi lekcji do listy.
                        "id": lesson.id, # ID lekcji.
                        "name": lesson.name, # Nazwa lekcji.
                        "order": lesson.order, # Kolejność lekcji.
                        "content": lesson.content # Treść lekcji.
                    })

                modules_data.append({ # Dodaje słownik z danymi modułu do listy `modules_data`.
                    "id": module.id, # ID modułu.
                    "title": module.name, # Nazwa modułu (użyto 'title' dla spójności z szablonem).
                    "lessons_completed": lessons_completed_in_module, # Liczba ukończonych lekcji w module.
                    "total_lessons": lessons_in_module, # Całkowita liczba lekcji w module.
                    "status": module_status, # Status modułu.
                    "gradient_class": module.gradient_class, # Klasa gradientu modułu.
                    "lessons_list": module_lessons_list # Lista szczegółów lekcji w module.
                })
                course_global_lessons_count += lessons_in_module # Aktualizuje globalny licznik lekcji w kursie.

            course_progress_percent = 0 # Inicjalizuje procent postępu kursu.
            if course.total_lessons > 0: # Sprawdza, czy kurs ma jakieś lekcje.
                course_progress_percent = (uc_rel.lessons_completed / course.total_lessons) * 100 # Oblicza procent ukończenia kursu.

            user_courses_data.append({ # Dodaje słownik z danymi kursu użytkownika do listy `user_courses_data`.
                "id": course.id, # ID kursu.
                "name": course.name, # Nazwa kursu.
                "description": course.description, # Opis kursu.
                "gradient_class": course.gradient_class, # Klasa gradientu kursu.
                "progress_lessons_completed": uc_rel.lessons_completed, # Liczba ukończonych lekcji w kursie przez użytkownika.
                "progress_total_lessons": course.total_lessons, # Całkowita liczba lekcji w kursie.
                "progress_percent": int(course_progress_percent), # Procent ukończenia kursu (jako liczba całkowita).
                "modules": modules_data, # Lista modułów kursu.
                "tabs": ["Na lekcji", "Zadanie domowe", "Ocena"], # Zakładki dla interfejsu użytkownika.
                "current_lesson_id": uc_rel.current_lesson_id # ID bieżącej lekcji użytkownika w tym kursie.
            })

    active_course_id = request.args.get('course_id') # Pobiera ID aktywnego kursu z parametrów zapytania URL.
    active_course = None # Inicjalizuje zmienną dla aktywnego kursu.
    if active_course_id: # Jeśli ID aktywnego kursu zostało podane w URL.
        for course_data in user_courses_data: # Iteruje przez dane kursów użytkownika.
            if str(course_data['id']) == active_course_id: # Sprawdza, czy ID kursu pasuje do aktywnego ID.
                active_course = course_data # Ustawia bieżący kurs jako aktywny.
                break # Przerywa pętlę.

    if not active_course and user_courses_data: # Jeśli nie ma aktywnego kursu w URL, ale użytkownik ma jakieś kursy.
        active_course = user_courses_data[0] # Ustawia pierwszy kurs użytkownika jako aktywny domyślnie.

    active_lesson_content = "Wybierz lekcję, aby zobaczyć jej zawartość." # Domyślna treść aktywnej lekcji.
    active_lesson_name = "Brak wybranej lekcji" # Domyślna nazwa aktywnej lekcji.

    if active_course and active_course['current_lesson_id']: # Jeśli istnieje aktywny kurs i ma ustawioną bieżącą lekcję.
        for module in active_course['modules']: # Iteruje przez moduły aktywnego kursu.
            for lesson in module['lessons_list']: # Iteruje przez lekcje w bieżącym module.
                if lesson['id'] == active_course['current_lesson_id']: # Sprawdza, czy ID lekcji pasuje do bieżącej lekcji użytkownika.
                    active_lesson_content = lesson['content'] # Ustawia treść aktywnej lekcji.
                    active_lesson_name = lesson['name'] # Ustawia nazwę aktywnej lekcji.
                    break # Przerywa wewnętrzną pętlę.
            if active_lesson_content != "Wybierz lekcję, aby zobaczyć jej zawartość.": # Jeśli treść lekcji została znaleziona.
                break # Przerywa zewnętrzną pętlę.
    elif active_course and active_course['modules']: # Jeśli istnieje aktywny kurs, ale nie ma ustawionej bieżącej lekcji, i ma moduły.
        if active_course['modules'][0]['lessons_list']: # Sprawdza, czy pierwszy moduł ma jakieś lekcje.
            first_lesson = active_course['modules'][0]['lessons_list'][0] # Pobiera pierwszą lekcję z pierwszego modułu.
            active_lesson_content = first_lesson['content'] # Ustawia treść aktywnej lekcji na treść pierwszej lekcji.
            active_lesson_name = first_lesson['name'] # Ustawia nazwę aktywnej lekcji na nazwę pierwszej lekcji.
            with app.app_context(): # Wchodzi w kontekst aplikacji.
                uc_rel_to_update = UserCourseAccess.query.filter_by(user_id=user_id, course_id=active_course['id']).first() # Znajduje rekord `UserCourseAccess` dla bieżącego użytkownika i aktywnego kursu.
                if uc_rel_to_update: # Jeśli rekord istnieje.
                    uc_rel_to_update.current_lesson_id = first_lesson['id'] # Ustawia `current_lesson_id` na ID pierwszej lekcji.
                    db.session.commit() # Zatwierdza zmiany w bazie danych.

    return render_template( # Renderuje szablon `learn.html`.
        'learn.html', # Plik szablonu do renderowania.
        user_courses=user_courses_data, # Przekazuje dane o kursach użytkownika do szablonu.
        active_course=active_course, # Przekazuje dane o aktywnym kursie do szablonu.
        username=current_user.username, # Przekazuje nazwę użytkownika do szablonu.
        lessons_balance=current_user.lessons_balance, # Przekazuje saldo lekcji użytkownika do szablonu.
        active_lesson_content=active_lesson_content, # Przekazuje treść aktywnej lekcji do szablonu.
        active_lesson_name=active_lesson_name, # Przekazuje nazwę aktywnej lekcji do szablonu.
        current_user=current_user # <--- WAŻNE: DODAJ TĘ LINIĘ # Przekazuje cały obiekt `current_user` do szablonu.
    )

# Trasa do aktualizacji bieżącej lekcji użytkownika w danym kursie
# Komentarz opisujący trasę aktualizacji bieżącej lekcji.
@app.route('/update_current_lesson', methods=['POST']) # Dekorator Flask, który mapuje URL '/update_current_lesson' do funkcji `update_current_lesson`. Akceptuje tylko metodę POST.
def update_current_lesson(): # Definiuje funkcję widoku `update_current_lesson`.
    if 'user_id' not in session: # Sprawdza, czy użytkownik jest zalogowany.
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401 # Zwraca błąd JSON i status 401, jeśli użytkownik nie jest zalogowany.

    user_id = session['user_id'] # Pobiera ID użytkownika z sesji.
    course_id = request.json.get('course_id') # Pobiera ID kursu z danych JSON żądania.
    lesson_id = request.json.get('lesson_id') # Pobiera ID lekcji z danych JSON żądania.

    if not course_id or not lesson_id: # Sprawdza, czy ID kursu lub lekcji są puste.
        return jsonify({'status': 'error', 'message': 'Missing course_id or lesson_id'}), 400 # Zwraca błąd JSON i status 400, jeśli brakuje danych.

    user_course_access = UserCourseAccess.query.filter_by(user_id=user_id, course_id=course_id).first() # Znajduje rekord dostępu użytkownika do kursu.
    if user_course_access: # Jeśli rekord dostępu istnieje.
        user_course_access.current_lesson_id = lesson_id # Aktualizuje `current_lesson_id` w rekordzie dostępu.

        current_lesson_obj = Lesson.query.get(lesson_id) # Pobiera obiekt bieżącej lekcji.
        if current_lesson_obj: # Jeśli obiekt lekcji istnieje.
            course = Course.query.get(course_id) # Pobiera obiekt kursu.

            lessons_in_course_ordered = [] # Inicjalizuje listę na posortowane lekcje w kursie.
            for module in sorted(course.modules, key=lambda m: m.order): # Iteruje przez moduły kursu posortowane według kolejności.
                lessons_in_course_ordered.extend(sorted(module.lessons, key=lambda l: l.order)) # Dodaje posortowane lekcje z każdego modułu do listy.

            lesson_global_order = -1 # Inicjalizuje globalny porządek lekcji.
            for i, l in enumerate(lessons_in_course_ordered): # Iteruje przez wszystkie lekcje w kursie, aby znaleźć globalny porządek bieżącej lekcji.
                if l.id == lesson_id: # Jeśli ID lekcji pasuje.
                    lesson_global_order = i + 1 # Ustawia globalny porządek lekcji.
                    break # Przerywa pętlę.

            if lesson_global_order != -1: # Jeśli globalny porządek lekcji został znaleziony.
                # Zwiększ lessons_completed tylko jeśli nowa lekcja ma wyższy porządek
                # Komentarz o warunku zwiększania `lessons_completed`.
                # i upewnij się, że nie przekracza całkowitej liczby lekcji w kursie
                # Komentarz o ograniczeniu `lessons_completed`.
                if user_course_access.lessons_completed < lesson_global_order: # Sprawdza, czy liczba ukończonych lekcji jest mniejsza niż globalny porządek nowej lekcji.
                    user_course_access.lessons_completed = min(lesson_global_order, course.total_lessons) # Aktualizuje `lessons_completed` do globalnego porządku nowej lekcji, ale nie więcej niż całkowita liczba lekcji w kursie.

        db.session.commit() # Zatwierdza zmiany w bazie danych.
        return jsonify({'status': 'success', 'message': 'Current lesson updated'}) # Zwraca sukces JSON.
    return jsonify({'status': 'error', 'message': 'User course not found'}), 404 # Zwraca błąd JSON i status 404, jeśli rekord dostępu nie został znaleziony.

# Pozostałe trasy (bez zmian w stosunku do poprzedniej wersji)
# Komentarz informujący o pozostałych trasach.
@app.route("/hire") # Dekorator Flask dla trasy '/hire'.
def hire(): # Definiuje funkcję widoku `hire`.
    return render_template("hire.html") # Renderuje szablon `hire.html`.

@app.route("/projects") # Dekorator Flask dla trasy '/projects'.
def projects(): # Definiuje funkcję widoku `projects`.
    return render_template("projects.html") # Renderuje szablon `projects.html`.

@app.route("/plan") # Dekorator Flask dla trasy '/plan'.
def plan(): # Definiuje funkcję widoku `plan`.
    return render_template("plan.html") # Renderuje szablon `plan.html`.

@app.route("/python") # Dekorator Flask dla trasy '/python'.
def python(): # Definiuje funkcję widoku `python`.
    return render_template("python.html") # Renderuje szablon `python.html`.

@app.route("/fullstack") # Dekorator Flask dla trasy '/fullstack'.
def full(): # Definiuje funkcję widoku `full`.
    return render_template("full.html") # Renderuje szablon `full.html`.

@app.route("/frontend") # Dekorator Flask dla trasy '/frontend'.
def frontend(): # Definiuje funkcję widoku `frontend`.
    return render_template("frontend.html") # Renderuje szablon `frontend.html`.

@app.route("/backend") # Dekorator Flask dla trasy '/backend'.
def backend(): # Definiuje funkcję widoku `backend`.
    return render_template("backend.html") # Renderuje szablon `backend.html`.

@app.route("/AI") # Dekorator Flask dla trasy '/AI'.
def AI(): # Definiuje funkcję widoku `AI`.
    return render_template("AI.html") # Renderuje szablon `AI.html`.

# --- ADMIN PANEL ROUTES ---
# Komentarz wprowadzający sekcję tras panelu administracyjnego.

@app.route('/admin') # Dekorator Flask dla trasy '/admin'.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_dashboard(): # Definiuje funkcję widoku `admin_dashboard`.
    total_users = User.query.count() # Liczy wszystkich użytkowników w bazie danych.
    total_courses = Course.query.count() # Liczy wszystkie kursy w bazie danych.
    total_lessons = Lesson.query.count() # Liczy wszystkie lekcje w bazie danych.
    return render_template('admin/dashboard.html', # Renderuje szablon `admin/dashboard.html`.
                            total_users=total_users, # Przekazuje całkowitą liczbę użytkowników.
                            total_courses=total_courses, # Przekazuje całkowitą liczbę kursów.
                            total_lessons=total_lessons) # Przekazuje całkowitą liczbę lekcji.

# --- Zarządzanie Użytkownikami ---
# Komentarz wprowadzający sekcję zarządzania użytkownikami.
@app.route('/admin/users') # Dekorator Flask dla trasy '/admin/users'.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_users(): # Definiuje funkcję widoku `admin_users`.
    users = User.query.all() # Pobiera wszystkich użytkowników z bazy danych.
    return render_template('admin/users.html', users=users) # Renderuje szablon `admin/users.html` i przekazuje listę użytkowników.

@app.route('/admin/users/add', methods=['GET', 'POST']) # Dekorator Flask dla trasy '/admin/users/add'. Akceptuje metody GET i POST.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_add_user(): # Definiuje funkcję widoku `admin_add_user`.
    if request.method == 'POST': # Sprawdza, czy żądanie HTTP jest typu POST.
        username = request.form['username'] # Pobiera nazwę użytkownika z formularza.
        email = request.form['email'] # Pobiera adres e-mail z formularza.
        password = request.form['password'] # Pobiera hasło z formularza.
        role = request.form.get('role', 'user') # Pobiera rolę użytkownika z formularza, domyślnie 'user'.
        lessons_balance = int(request.form.get('lessons_balance', 0)) # Pobiera saldo lekcji z formularza, domyślnie 0.

        if User.query.filter_by(username=username).first(): # Sprawdza, czy nazwa użytkownika już istnieje.
            flash('Nazwa użytkownika już istnieje!', 'danger') # Wyświetla komunikat o błędzie.
        elif User.query.filter_by(email=email).first(): # Sprawdza, czy adres e-mail już istnieje.
            flash('Email już istnieje!', 'danger') # Wyświetla komunikat o błędzie.
        else: # Jeśli nazwa użytkownika i e-mail są unikalne.
            hashed_password = generate_password_hash(password) # Haszuje podane hasło.
            new_user = User(username=username, email=email, password_hash=hashed_password, # Tworzy nowy obiekt `User`.
                            role=role, lessons_balance=lessons_balance) # Ustawia rolę i saldo lekcji.
            db.session.add(new_user) # Dodaje nowego użytkownika do sesji bazy danych.
            db.session.commit() # Zatwierdza zmiany w bazie danych.
            flash('Użytkownik dodany pomyślnie!', 'success') # Wyświetla komunikat o sukcesie.
            return redirect(url_for('admin_users')) # Przekierowuje do listy użytkowników.
    return render_template('admin/add_user.html') # Renderuje szablon `admin/add_user.html` (dla żądań GET lub nieudanych POST).

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST']) # Dekorator Flask dla trasy edycji użytkownika.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_edit_user(user_id): # Definiuje funkcję widoku `admin_edit_user`.
    user = User.query.get_or_404(user_id) # Pobiera użytkownika po ID lub zwraca błąd 404.
    if request.method == 'POST': # Sprawdza, czy żądanie HTTP jest typu POST.
        user.username = request.form['username'] # Aktualizuje nazwę użytkownika.
        user.email = request.form['email'] # Aktualizuje adres e-mail.
        user.role = request.form['role'] # Aktualizuje rolę.
        user.lessons_balance = int(request.form['lessons_balance']) # Aktualizuje saldo lekcji.
        if request.form['password']: # Sprawdza, czy podano nowe hasło.
            user.password_hash = generate_password_hash(request.form['password']) # Haszuje i aktualizuje hasło.
        db.session.commit() # Zatwierdza zmiany w bazie danych.
        flash('Użytkownik zaktualizowany pomyślnie!', 'success') # Wyświetla komunikat o sukcesie.
        return redirect(url_for('admin_users')) # Przekierowuje do listy użytkowników.
    return render_template('admin/edit_user.html', user=user) # Renderuje szablon `admin/edit_user.html` i przekazuje obiekt użytkownika.

@app.route('/admin/users/delete/<int:user_id>', methods=['POST']) # Dekorator Flask dla trasy usuwania użytkownika.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_delete_user(user_id): # Definiuje funkcję widoku `admin_delete_user`.
    user = User.query.get_or_404(user_id) # Pobiera użytkownika po ID lub zwraca błąd 404.
    # Usuń powiązane UserCourseAccess przed usunięciem użytkownika (kaskadowe usuwanie w models.py powinno to zrobić, ale to jest bezpieczniejsze)
    # Komentarz o usuwaniu powiązanych rekordów.
    UserCourseAccess.query.filter_by(user_id=user.id).delete() # Usuwa wszystkie rekordy `UserCourseAccess` powiązane z tym użytkownikiem.
    db.session.delete(user) # Usuwa obiekt użytkownika z sesji bazy danych.
    db.session.commit() # Zatwierdza zmiany w bazie danych.
    flash('Użytkownik usunięty pomyślnie!', 'success') # Wyświetla komunikat o sukcesie.
    return redirect(url_for('admin_users')) # Przekierowuje do listy użytkowników.

@app.route('/admin/users/assign_course/<int:user_id>', methods=['GET', 'POST']) # Dekorator Flask dla trasy przypisywania kursu do użytkownika.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_assign_course_to_user(user_id): # Definiuje funkcję widoku `admin_assign_course_to_user`.
    user = User.query.get_or_404(user_id) # Pobiera użytkownika po ID lub zwraca błąd 404.
    all_courses = Course.query.all() # Pobiera wszystkie dostępne kursy.
    user_assigned_course_ids = [uc.course_id for uc in user.course_accesses] # Tworzy listę ID kursów, do których użytkownik już ma dostęp.

    if request.method == 'POST': # Sprawdza, czy żądanie HTTP jest typu POST.
        course_id_to_assign = request.form.get('course_id') # Pobiera ID kursu do przypisania z formularza.
        if course_id_to_assign: # Sprawdza, czy ID kursu zostało wybrane.
            course_id_to_assign = int(course_id_to_assign) # Konwertuje ID kursu na liczbę całkowitą.
            existing_access = UserCourseAccess.query.filter_by(user_id=user.id, course_id=course_id_to_assign).first() # Sprawdza, czy użytkownik już ma dostęp do tego kursu.
            if not existing_access: # Jeśli użytkownik nie ma jeszcze dostępu do tego kursu.
                new_access = UserCourseAccess(user_id=user.id, course_id=course_id_to_assign, lessons_completed=0, current_lesson_id=None) # Tworzy nowy rekord dostępu.
                db.session.add(new_access) # Dodaje nowy rekord do sesji bazy danych.
                db.session.commit() # Zatwierdza zmiany.
                flash(f'Dostęp do kursu {Course.query.get(course_id_to_assign).name} nadany użytkownikowi {user.username}.', 'success') # Wyświetla komunikat o sukcesie.
            else: # Jeśli użytkownik już ma dostęp do tego kursu.
                flash(f'Użytkownik {user.username} już ma dostęp do tego kursu.', 'warning') # Wyświetla komunikat ostrzegawczy.
        else: # Jeśli nie wybrano kursu.
            flash('Wybierz kurs do przypisania.', 'danger') # Wyświetla komunikat o błędzie.
        return redirect(url_for('admin_assign_course_to_user', user_id=user.id)) # Przekierowuje z powrotem na stronę przypisywania kursów.

    return render_template('admin/assign_course_to_user.html', # Renderuje szablon `admin/assign_course_to_user.html`.
                            user=user, # Przekazuje obiekt użytkownika.
                            all_courses=all_courses, # Przekazuje listę wszystkich kursów.
                            user_assigned_course_ids=user_assigned_course_ids) # Przekazuje listę ID przypisanych kursów.

@app.route('/admin/users/revoke_course/<int:user_id>/<int:course_id>', methods=['POST']) # Dekorator Flask dla trasy odbierania dostępu do kursu.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_revoke_course_from_user(user_id, course_id): # Definiuje funkcję widoku `admin_revoke_course_from_user`.
    user_course_access = UserCourseAccess.query.filter_by(user_id=user_id, course_id=course_id).first_or_404() # Pobiera rekord dostępu lub zwraca błąd 404.
    user = User.query.get(user_id) # Pobiera obiekt użytkownika.
    course = Course.query.get(course_id) # Pobiera obiekt kursu.
    db.session.delete(user_course_access) # Usuwa rekord dostępu z sesji bazy danych.
    db.session.commit() # Zatwierdza zmiany.
    flash(f'Dostęp do kursu {course.name} odebrany użytkownikowi {user.username}.', 'info') # Wyświetla komunikat informacyjny.
    return redirect(url_for('admin_assign_course_to_user', user_id=user.id)) # Przekierowuje z powrotem na stronę przypisywania kursów.

# --- Zarządzanie Kursami ---
# Komentarz wprowadzający sekcję zarządzania kursami.
@app.route('/admin/courses') # Dekorator Flask dla trasy '/admin/courses'.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_courses(): # Definiuje funkcję widoku `admin_courses`.
    courses = Course.query.all() # Pobiera wszystkie kursy z bazy danych.
    return render_template('admin/courses.html', courses=courses) # Renderuje szablon `admin/courses.html` i przekazuje listę kursów.

@app.route('/admin/courses/add', methods=['GET', 'POST']) # Dekorator Flask dla trasy dodawania kursu.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_add_course(): # Definiuje funkcję widoku `admin_add_course`.
    if request.method == 'POST': # Sprawdza, czy żądanie HTTP jest typu POST.
        name = request.form['name'] # Pobiera nazwę kursu z formularza.
        description = request.form['description'] # Pobiera opis kursu z formularza.
        gradient_class = request.form.get('gradient_class', 'course-gradient-default') # Pobiera klasę gradientu, domyślnie 'course-gradient-default'.

        modules = request.form.getlist('module_name[]') # Pobiera listę nazw modułów z formularza.
        lessons_counts = request.form.getlist('module_lessons[]') # Pobiera listę liczby lekcji dla każdego modułu z formularza.

        new_course = Course(name=name, description=description, gradient_class=gradient_class, total_lessons=0) # Tworzy nowy obiekt `Course`.
        db.session.add(new_course) # Dodaje nowy kurs do sesji bazy danych.
        db.session.commit() # Zatwierdza kurs, aby otrzymał ID.

        total_lessons_in_course = 0 # Inicjalizuje licznik całkowitej liczby lekcji w kursie.
        for index, module_name in enumerate(modules): # Iteruje przez moduły i ich indeksy.
            lesson_count = int(lessons_counts[index]) # Pobiera liczbę lekcji dla bieżącego modułu.
            total_lessons_in_course += lesson_count # Dodaje liczbę lekcji modułu do sumy lekcji w kursie.

            module = Module( # Tworzy nowy obiekt `Module`.
                name=module_name, # Ustawia nazwę modułu.
                course_id=new_course.id, # Przypisuje moduł do nowo utworzonego kursu.
                order=index + 1, # Ustawia kolejność modułu.
                total_lessons=lesson_count, # Ustawia całkowitą liczbę lekcji w module.
                gradient_class='module-gradient-default' # Ustawia domyślną klasę gradientu modułu.
            )
            db.session.add(module) # Dodaje nowy moduł do sesji bazy danych.
            db.session.commit() # Zatwierdza moduł, aby otrzymał ID.

            for lesson_order in range(1, lesson_count + 1): # Iteruje, aby dodać lekcje do modułu.
                lesson = Lesson( # Tworzy nowy obiekt `Lesson`.
                    name=f"Lekcja {index + 1}.{lesson_order}", # Generuje nazwę lekcji.
                    content=f"Treść lekcji {lesson_order} w module {module_name}.", # Generuje treść lekcji.
                    order=lesson_order, # Ustawia kolejność lekcji.
                    module_id=module.id # Przypisuje lekcję do bieżącego modułu.
                )
                db.session.add(lesson) # Dodaje nową lekcję do sesji bazy danych.

        new_course.total_lessons = total_lessons_in_course # Aktualizuje całkowitą liczbę lekcji dla kursu.
        db.session.commit() # Zatwierdza wszystkie lekcje i zaktualizowany kurs.

        flash('Kurs wraz z modułami i lekcjami dodany pomyślnie!', 'success') # Wyświetla komunikat o sukcesie.
        return redirect(url_for('admin_courses')) # Przekierowuje do listy kursów.

    return render_template('admin/add_course.html') # Renderuje szablon `admin/add_course.html`.


@app.route('/admin/courses/edit/<int:course_id>', methods=['GET', 'POST']) # Dekorator Flask dla trasy edycji kursu.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_edit_course(course_id): # Definiuje funkcję widoku `admin_edit_course`.
    course = Course.query.get_or_404(course_id) # Pobiera kurs po ID lub zwraca błąd 404.
    if request.method == 'POST': # Sprawdza, czy żądanie HTTP jest typu POST.
        course.name = request.form['name'] # Aktualizuje nazwę kursu.
        course.description = request.form['description'] # Aktualizuje opis kursu.
        course.gradient_class = request.form.get('gradient_class', 'course-gradient-default') # Aktualizuje klasę gradientu.
        db.session.commit() # Zatwierdza zmiany.
        flash('Kurs zaktualizowany pomyślnie!', 'success') # Wyświetla komunikat o sukcesie.
        return redirect(url_for('admin_courses')) # Przekierowuje do listy kursów.
    return render_template('admin/edit_course.html', course=course) # Renderuje szablon `admin/edit_course.html` i przekazuje obiekt kursu.

@app.route('/admin/courses/delete/<int:course_id>', methods=['POST']) # Dekorator Flask dla trasy usuwania kursu.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_delete_course(course_id): # Definiuje funkcję widoku `admin_delete_course`.
    course = Course.query.get_or_404(course_id) # Pobiera kurs po ID lub zwraca błąd 404.
    # Usuń powiązane UserCourseAccess, moduły i lekcje
    # Komentarz o usuwaniu powiązanych rekordów.
    UserCourseAccess.query.filter_by(course_id=course.id).delete() # Usuwa wszystkie rekordy `UserCourseAccess` powiązane z tym kursem.
    for module in course.modules: # Iteruje przez moduły kursu.
        Lesson.query.filter_by(module_id=module.id).delete() # Usuwa wszystkie lekcje powiązane z modułem.
    Module.query.filter_by(course_id=course.id).delete() # Usuwa wszystkie moduły powiązane z kursem.

    db.session.delete(course) # Usuwa obiekt kursu z sesji bazy danych.
    db.session.commit() # Zatwierdza zmiany.
    flash('Kurs usunięty pomyślnie!', 'success') # Wyświetla komunikat o sukcesie.
    return redirect(url_for('admin_courses')) # Przekierowuje do listy kursów.

# --- Zarządzanie Modułami ---
# Komentarz wprowadzający sekcję zarządzania modułami.
@app.route('/admin/modules') # Dekorator Flask dla trasy '/admin/modules'.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_modules(): # Definiuje funkcję widoku `admin_modules`.
    modules = Module.query.order_by(Module.course_id, Module.order).all() # Pobiera wszystkie moduły, posortowane według ID kursu i kolejności.
    courses = Course.query.all() # Pobiera wszystkie kursy.
    return render_template('admin/modules.html', modules=modules, courses=courses) # Renderuje szablon `admin/modules.html` i przekazuje moduły oraz kursy.

@app.route('/admin/modules/add', methods=['GET', 'POST']) # Dekorator Flask dla trasy dodawania modułu.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_add_module(): # Definiuje funkcję widoku `admin_add_module`.
    courses = Course.query.all() # Pobiera wszystkie dostępne kursy.
    if request.method == 'POST': # Sprawdza, czy żądanie HTTP jest typu POST.
        name = request.form['name'] # Zmieniono z 'title' na 'name' # Pobiera nazwę modułu z formularza.
        order = int(request.form['order']) # Pobiera kolejność modułu z formularza.
        course_id = int(request.form['course_id']) # Pobiera ID kursu z formularza.
        gradient_class = request.form.get('gradient_class', 'module-gradient-default') # Pobiera klasę gradientu, domyślnie 'module-gradient-default'.
        new_module = Module(name=name, order=order, course_id=course_id, gradient_class=gradient_class, total_lessons=0) # Tworzy nowy obiekt `Module`.
        db.session.add(new_module) # Dodaje nowy moduł do sesji bazy danych.
        db.session.commit() # Zatwierdza moduł, aby otrzymał ID.

        # Zaktualizuj total_lessons w Course po dodaniu modułu
        # Komentarz o aktualizacji `total_lessons` w kursie.
        course = Course.query.get(course_id) # Pobiera obiekt kursu, do którego dodano moduł.
        if course: # Jeśli kurs istnieje.
            course.total_lessons = sum(m.total_lessons for m in course.modules) # Aktualizuje `total_lessons` w kursie, sumując `total_lessons` wszystkich jego modułów.
            db.session.commit() # Zatwierdza zmiany w kursie.

        flash('Moduł dodany pomyślnie!', 'success') # Wyświetla komunikat o sukcesie.
        return redirect(url_for('admin_modules')) # Przekierowuje do listy modułów.
    return render_template('admin/add_module.html', courses=courses) # Renderuje szablon `admin/add_module.html` i przekazuje listę kursów.

@app.route('/admin/modules/edit/<int:module_id>', methods=['GET', 'POST']) # Dekorator Flask dla trasy edycji modułu.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_edit_module(module_id): # Definiuje funkcję widoku `admin_edit_module`.
    module = Module.query.get_or_404(module_id) # Pobiera moduł po ID lub zwraca błąd 404.
    courses = Course.query.all() # Pobiera wszystkie dostępne kursy.
    if request.method == 'POST': # Sprawdza, czy żądanie HTTP jest typu POST.
        old_course_id = module.course_id # Zapamiętaj stary kurs, jeśli moduł zostanie przeniesiony # Zapisuje ID starego kursu modułu.
        module.name = request.form['name'] # Zmieniono z 'title' na 'name' # Aktualizuje nazwę modułu.
        module.order = int(request.form['order']) # Aktualizuje kolejność modułu.
        module.course_id = int(request.form['course_id']) # Aktualizuje ID kursu, do którego należy moduł.
        module.gradient_class = request.form.get('gradient_class', 'module-gradient-default') # Aktualizuje klasę gradientu.
        db.session.commit() # Zatwierdza zmiany w module.

        # Zaktualizuj total_lessons w kursach, jeśli moduł został przeniesiony
        # Komentarz o aktualizacji `total_lessons` w kursach.
        if old_course_id != module.course_id: # Sprawdza, czy moduł został przeniesiony do innego kursu.
            old_course = Course.query.get(old_course_id) # Pobiera stary obiekt kursu.
            if old_course: # Jeśli stary kurs istnieje.
                old_course.total_lessons = sum(m.total_lessons for m in old_course.modules) # Aktualizuje `total_lessons` w starym kursie.
                db.session.commit() # Zatwierdza zmiany w starym kursie.

        new_course = Course.query.get(module.course_id) # Pobiera nowy obiekt kursu.
        if new_course: # Jeśli nowy kurs istnieje.
            new_course.total_lessons = sum(m.total_lessons for m in new_course.modules) # Aktualizuje `total_lessons` w nowym kursie.
            db.session.commit() # Zatwierdza zmiany w nowym kursie.

        flash('Moduł zaktualizowany pomyślnie!', 'success') # Wyświetla komunikat o sukcesie.
        return redirect(url_for('admin_modules')) # Przekierowuje do listy modułów.
    return render_template('admin/edit_module.html', module=module, courses=courses) # Renderuje szablon `admin/edit_module.html` i przekazuje obiekt modułu oraz listę kursów.

@app.route('/admin/modules/delete/<int:module_id>', methods=['POST']) # Dekorator Flask dla trasy usuwania modułu.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_delete_module(module_id): # Definiuje funkcję widoku `admin_delete_module`.
    module = Module.query.get_or_404(module_id) # Pobiera moduł po ID lub zwraca błąd 404.
    course_id = module.course_id # Zapamiętaj ID kursu, aby zaktualizować total_lessons # Zapisuje ID kursu, do którego należał moduł.

    # Usuń powiązane lekcje przed usunięciem modułu
    # Komentarz o usuwaniu powiązanych lekcji.
    Lesson.query.filter_by(module_id=module.id).delete() # Usuwa wszystkie lekcje powiązane z tym modułem.
    db.session.delete(module) # Usuwa obiekt modułu z sesji bazy danych.
    db.session.commit() # Zatwierdza zmiany.

    # Zaktualizuj total_lessons w Course
    # Komentarz o aktualizacji `total_lessons` w kursie.
    course = Course.query.get(course_id) # Pobiera obiekt kursu.
    if course: # Jeśli kurs istnieje.
        course.total_lessons = sum(m.total_lessons for m in course.modules) # Aktualizuje `total_lessons` w kursie, sumując `total_lessons` pozostałych modułów.
        db.session.commit() # Zatwierdza zmiany w kursie.

    flash('Moduł usunięty pomyślnie!', 'success') # Wyświetla komunikat o sukcesie.
    return redirect(url_for('admin_modules')) # Przekierowuje do listy modułów.

# --- Zarządzanie Lekcjami ---
# Komentarz wprowadzający sekcję zarządzania lekcjami.
@app.route('/admin/lessons') # Dekorator Flask dla trasy '/admin/lessons'.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_lessons(): # Definiuje funkcję widoku `admin_lessons`.
    lessons = Lesson.query.order_by(Lesson.module_id, Lesson.order).all() # Pobiera wszystkie lekcje, posortowane według ID modułu i kolejności.
    modules = Module.query.all() # Pobiera wszystkie moduły.
    return render_template('admin/lessons.html', lessons=lessons, modules=modules) # Renderuje szablon `admin/lessons.html` i przekazuje lekcje oraz moduły.

@app.route('/admin/lessons/add', methods=['GET', 'POST']) # Dekorator Flask dla trasy dodawania lekcji.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_add_lesson(): # Definiuje funkcję widoku `admin_add_lesson`.
    modules = Module.query.all() # Pobiera wszystkie dostępne moduły.
    if request.method == 'POST': # Sprawdza, czy żądanie HTTP jest typu POST.
        name = request.form['name'] # Pobiera nazwę lekcji z formularza.
        content = request.form['content'] # Pobiera treść lekcji z formularza.
        order = int(request.form['order']) # Pobiera kolejność lekcji z formularza.
        module_id = int(request.form['module_id']) # Pobiera ID modułu z formularza.
        new_lesson = Lesson(name=name, content=content, order=order, module_id=module_id) # Tworzy nowy obiekt `Lesson`.
        db.session.add(new_lesson) # Dodaje nową lekcję do sesji bazy danych.
        db.session.commit() # Zatwierdza lekcję.

        # Zaktualizuj total_lessons w Module i Course
        # Komentarz o aktualizacji `total_lessons` w module i kursie.
        module = Module.query.get(module_id) # Pobiera obiekt modułu, do którego dodano lekcję.
        if module: # Jeśli moduł istnieje.
            module.total_lessons = Lesson.query.filter_by(module_id=module_id).count() # Aktualizuje `total_lessons` w module, licząc lekcje w nim.
            db.session.commit() # Zatwierdza zmiany w module.
            if module.course: # Jeśli moduł jest powiązany z kursem.
                course = module.course # Pobiera obiekt kursu.
                course.total_lessons = sum(m.total_lessons for m in course.modules) # Aktualizuje `total_lessons` w kursie.
                db.session.commit() # Zatwierdza zmiany w kursie.

        flash('Lekcja dodana pomyślnie!', 'success') # Wyświetla komunikat o sukcesie.
        return redirect(url_for('admin_lessons')) # Przekierowuje do listy lekcji.
    return render_template('admin/add_lesson.html', modules=modules) # Renderuje szablon `admin/add_lesson.html` i przekazuje listę modułów.

@app.route('/admin/lessons/edit/<int:lesson_id>', methods=['GET', 'POST']) # Dekorator Flask dla trasy edycji lekcji.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_edit_lesson(lesson_id): # Definiuje funkcję widoku `admin_edit_lesson`.
    lesson = Lesson.query.get_or_404(lesson_id) # Pobiera lekcję po ID lub zwraca błąd 404.
    modules = Module.query.all() # Pobiera wszystkie dostępne moduły.
    if request.method == 'POST': # Sprawdza, czy żądanie HTTP jest typu POST.
        old_module_id = lesson.module_id # Zapisuje ID starego modułu lekcji.
        lesson.name = request.form['name'] # Aktualizuje nazwę lekcji.
        lesson.content = request.form['content'] # Aktualizuje treść lekcji.
        lesson.order = int(request.form['order']) # Aktualizuje kolejność lekcji.
        lesson.module_id = int(request.form['module_id']) # Aktualizuje ID modułu, do którego należy lekcja.
        db.session.commit() # Zatwierdza zmiany w lekcji.

        # Zaktualizuj total_lessons w modułach i kursach
        # Komentarz o aktualizacji `total_lessons` w modułach i kursach.
        if old_module_id != lesson.module_id: # Sprawdza, czy lekcja została przeniesiona do innego modułu.
            old_module = Module.query.get(old_module_id) # Pobiera stary obiekt modułu.
            if old_module: # Jeśli stary moduł istnieje.
                old_module.total_lessons = Lesson.query.filter_by(module_id=old_module_id).count() # Aktualizuje `total_lessons` w starym module.
                db.session.commit() # Zatwierdza zmiany w starym module.
                if old_module.course: # Jeśli stary moduł jest powiązany z kursem.
                    old_module.course.total_lessons = sum(m.total_lessons for m in old_module.course.modules) # Aktualizuje `total_lessons` w kursie starego modułu.
                    db.session.commit() # Zatwierdza zmiany w kursie.

        new_module = Module.query.get(lesson.module_id) # Pobiera nowy obiekt modułu.
        if new_module: # Jeśli nowy moduł istnieje.
            new_module.total_lessons = Lesson.query.filter_by(module_id=lesson.module_id).count() # Aktualizuje `total_lessons` w nowym module.
            db.session.commit() # Zatwierdza zmiany w nowym module.
            if new_module.course: # Jeśli nowy moduł jest powiązany z kursem.
                new_module.course.total_lessons = sum(m.total_lessons for m in new_module.course.modules) # Aktualizuje `total_lessons` w kursie nowego modułu.
                db.session.commit() # Zatwierdza zmiany w kursie.

        flash('Lekcja zaktualizowana pomyślnie!', 'success') # Wyświetla komunikat o sukcesie.
        return redirect(url_for('admin_lessons')) # Przekierowuje do listy lekcji.
    return render_template('admin/edit_lesson.html', lesson=lesson, modules=modules) # Renderuje szablon `admin/edit_lesson.html` i przekazuje obiekt lekcji oraz listę modułów.

@app.route('/admin/lessons/delete/<int:lesson_id>', methods=['POST']) # Dekorator Flask dla trasy usuwania lekcji.
@admin_required # Dekorator `admin_required` upewnia się, że tylko administratorzy mają dostęp.
def admin_delete_lesson(lesson_id): # Definiuje funkcję widoku `admin_delete_lesson`.

    lesson = Lesson.query.get_or_404(lesson_id) # Pobiera lekcję po ID lub zwraca błąd 404.
    module_id = lesson.module_id # Zapisuje ID modułu, do którego należała lekcja.
    db.session.delete(lesson) # Usuwa obiekt lekcji z sesji bazy danych.
    db.session.commit() # Zatwierdza zmiany.

    # Zaktualizuj total_lessons w Module i Course
    # Komentarz o aktualizacji `total_lessons` w module i kursie.
    module = Module.query.get(module_id) # Pobiera obiekt modułu.
    if module: # Jeśli moduł istnieje.
        module.total_lessons = Lesson.query.filter_by(module_id=module_id).count() # Aktualizuje `total_lessons` w module.
        db.session.commit() # Zatwierdza zmiany w module.
        if module.course: # Jeśli moduł jest powiązany z kursem.
            course = module.course # Pobiera obiekt kursu.
            course.total_lessons = sum(m.total_lessons for m in course.modules) # Aktualizuje `total_lessons` w kursie.
            db.session.commit() # Zatwierdza zmiany w kursie.

    flash('Lekcja usunięta pomyślnie!', 'success') # Wyświetla komunikat o sukcesie.
    return redirect(url_for('admin_lessons')) # Przekierowuje do listy lekcji.

@app.route('/enroll/<string:course_name>') # Dekorator Flask dla trasy zapisu na kurs.
@is_logged_in # Dekorator `is_logged_in` upewnia się, że użytkownik jest zalogowany.
def enroll_course(course_name): # Definiuje funkcję widoku `enroll_course`.
    user_id = session['user_id'] # Pobiera ID użytkownika z sesji.
    user = User.query.get(user_id) # Pobiera obiekt użytkownika.
    course = Course.query.filter_by(name=course_name).first() # Szuka kursu po nazwie.

    if not user: # Sprawdza, czy użytkownik istnieje (choć `is_logged_in` już to zapewnia).
        flash('Musisz być zalogowany, aby zapisać się na kurs.', 'warning') # Wyświetla komunikat ostrzegawczy.
        return redirect(url_for('login')) # Przekierowuje do logowania.

    if not course: # Sprawdza, czy kurs o podanej nazwie istnieje.
        flash('Kurs o podanej nazwie nie istnieje.', 'error') # Wyświetla komunikat o błędzie.
        return redirect(url_for('learn')) # Przekierowuje do strony nauki, jeśli kurs nie znaleziony.

    # Sprawdź, czy użytkownik już jest zapisany na ten kurs
    # Komentarz o sprawdzaniu istniejącego dostępu.
    existing_access = UserCourseAccess.query.filter_by(user_id=user.id, course_id=course.id).first() # Sprawdza, czy istnieje rekord `UserCourseAccess` dla tego użytkownika i kursu.

    if existing_access: # Jeśli użytkownik już jest zapisany na kurs.
        flash(f'Jesteś już zapisany na kurs "{course.name}".', 'info') # Wyświetla komunikat informacyjny.
    else: # Jeśli użytkownik nie jest jeszcze zapisany.
        # Tworzenie nowego rekordu dostępu użytkownika do kursu
        # Komentarz o tworzeniu nowego rekordu.
        new_access = UserCourseAccess(user_id=user.id, course_id=course.id, lessons_completed=0, current_lesson_id=None) # Tworzy nowy rekord `UserCourseAccess`.
        db.session.add(new_access) # Dodaje nowy rekord do sesji bazy danych.
        db.session.commit() # Zatwierdza zmiany.
        flash(f'Pomyślnie zapisano na kurs "{course.name}"!', 'success') # Wyświetla komunikat o sukcesie.

    # Po zapisaniu (lub jeśli już był zapisany), przekieruj użytkownika do strony nauki dla tego kursu
    # Komentarz o przekierowaniu po zapisaniu.
    return redirect(url_for('learn', course_id=course.id)) # Przekierowuje użytkownika na stronę nauki, z aktywnym kursem ustawionym na nowo zapisany kurs.



# === Uruchomienie aplikacji Flask ===
# Komentarz wprowadzający sekcję uruchamiania aplikacji.
if __name__ == '__main__': # Standardowa konstrukcja Pythona, która zapewnia, że kod w tym bloku zostanie uruchomiony tylko wtedy, gdy skrypt jest uruchamiany bezpośrednio (nie importowany jako moduł).
    # Ta sekcja zostanie uruchomiona tylko wtedy, gdy plik main.py jest uruchamiany bezpośrednio
    # a nie importowany jako moduł.
    # Komentarz wyjaśniający warunek `if __name__ == '__main__':`.

    # --- WAŻNE: WŁĄCZAMY init_db_and_data TYLKO NA LOKALNYM DEVELOPMENTIE ---
    # Komentarz podkreślający warunkowe uruchamianie `init_db_and_data`.
    # Na produkcji (Render.com) nie chcesz, aby to uruchamiało się za każdym razem,
    # gdy aplikacja startuje, bo to mogłoby nadpisać dane lub spowodować błędy.
    # Komentarz wyjaśniający powody warunku.
    # Używamy zmiennej środowiskowej FLASK_ENV do kontroli.
    # Komentarz o zmiennej środowiskowej `FLASK_ENV`.
    # Na Renderze ustaw FLASK_ENV na 'production'.
    # Komentarz o ustawieniu `FLASK_ENV` na Render.com.
    with app.app_context(): # Wchodzi w kontekst aplikacji Flask, co jest niezbędne do interakcji z bazą danych poza kontekstem żądania.
        if os.environ.get('FLASK_ENV') != 'production': # Sprawdza, czy zmienna środowiskowa 'FLASK_ENV' NIE jest ustawiona na 'production'.
             init_db_and_data() # Jeśli nie jest 'production' (czyli prawdopodobnie development), wywołuje funkcję do inicjalizacji bazy danych i dodawania przykładowych danych.
        else: # Jeśli 'FLASK_ENV' jest ustawione na 'production'.
            # Na produkcji, upewnij się, że tabele są tworzone (jeśli jeszcze nie istnieją)
            # Komentarz o tworzeniu tabel na produkcji.
            # ale bez dodawania przykładowych danych, aby nie nadpisywać.
            # Komentarz o braku dodawania przykładowych danych.
            # Zwykle to robi się przez narzędzia do migracji bazy danych (np. Flask-Migrate).
            # Komentarz o narzędziach do migracji.
            db.create_all() # Tworzy wszystkie tabele w bazie danych, jeśli jeszcze nie istnieją. Na produkcji nie dodaje danych, tylko upewnia się, że struktura jest gotowa.
            print("Aplikacja uruchomiona w trybie produkcyjnym. Baza danych sprawdzona/utworzona.") # Wyświetla komunikat o uruchomieniu w trybie produkcyjnym.


    # --- WAŻNE: DEBUG=TRUE TYLKO DLA DEVELOPMENTU ---
    # Komentarz podkreślający warunkowe ustawienie trybu debugowania.
    # Nigdy nie uruchamiaj aplikacji na produkcji z debug=True!
    # Komentarz o bezpieczeństwie.
    # Na Renderze aplikacja będzie uruchamiana przez Gunicorn, który zarządza procesami,
    # Komentarz o Gunicornie na Render.com.
    # więc ten blok 'if __name__ == "__main__":' i tak nie będzie używany do uruchomienia serwera.
    # Komentarz wyjaśniający, że ten blok nie uruchamia serwera na produkcji.
    # Ale dla pewności, zmieniamy debug na dynamiczny.
    # Komentarz o dynamicznym debugowaniu.
    app.run(debug=os.environ.get('FLASK_ENV') != 'production') # debug=False na produkcji # Uruchamia serwer deweloperski Flask. `debug` jest ustawiony na True, jeśli `FLASK_ENV` nie jest 'production', w przeciwnym razie na False.
