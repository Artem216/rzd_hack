## 👨🏻‍💻 Региональный Цифровой Прорыв, 2024 
🙋🏻‍♂️ Решение команды **MISIS Dark Horse** | 2 место 🥈  
⚛️ Кейс - Создание модели формирования и прогнозирования рейтинга эффективности парков транспортных средств подразделений компании.

### Описание задачи

В рамках кейсового задания выполняется разработка программного алгоритма, способного в кратчайшие сроки обрабатывать большие объемы данных, формируемых в различных системах учета ОАО «РЖД» и формировать аналитические отчеты по эксплуатации парка транспортных средств балансодержателями, с группировкой по уровням управления (от структурных подразделений до центральных дирекций функциональных филиалов). На основании анализируемых данных алгоритм должен осуществлять формирование и прогноз рейтинга эффективности эксплуатации парков транспортных средств.

### Наше решение

Наше решение включает в себя модель машинного обучения, которая позволяет предсказывать рейтинг подразделения через определенный срок, и удобный сервис, где можно будет выбрать на сколько впередмы хотим делать предсказания. Так же на сервисе можно будет смотреть на информативные дашборды, которые помогут анализировать простой автотранспорта, сравнивать между собой полигоны и отделения. Возможность накладывать фильтры на данные по всем значениям и уже смотреть на графики для конкретного подмножества.
Стек решения: streamlit, python, sklearn
Уникальность нашего решения в том, что можно выбирать срок на который мы хотим делать прогноз нашей оценки. Так же мы предлагаем другой формат оценки, который позволит не дискретизировать коэффициенты, а сделать их непрерывными

### ML

[Data Prepare](<./ml/Data%20Prepare%20(4).ipynb>) - подготовка данных и моделинг  
[number_of_cars](./ml/number_of_cars.ipynb) - анализ машин и их использования  
[Prepare_func](<./ml/prepare_func%20(3).ipynb>) - то же что и первый файл, только с правками

### Пример работы

![work1](https://github.com/Artem216/rzd_hack/blob/main/imgs/работа1.png)

![work2](https://github.com/Artem216/rzd_hack/blob/main/imgs/работа2.png)

![work2](https://github.com/Artem216/rzd_hack/blob/main/imgs/работа3.png)

### Сервис

Запустить локально  
docker compose up --build -d

Пользователь Admin доступны данные по всем отделениям и есть возможность загружать данные  
Логин: admin  
Пароль: admin

Пользователь Test доступны данные только по структурному подразделению **"Московская механизированная дистанция погрузочно-разгрузочных рабо#"** нет возможности загружать данные  
Логин: test  
Пароль: test

### Состав команды
**Николай Александров** - Data Scientist   
**Сергей Мартынов** - Data Scientist, Design   
**Кирилл Шаповалов** - Analytic, Design    
**Артем Цыканов** - Data Scientist, Frontend, Backend  
**Роман Шабаев** - Backend
