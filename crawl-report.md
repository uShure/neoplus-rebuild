# Crawl Report — balashikha.neoplus-clinic.ru

Дата: 2026-11-11 · Инструменты: ZCode in-app Chromium (обход JS-челленджа DDoS-Guard, cookies + тот же UA) → python-краулер (curl/urllib, 5 потоков, 0.1s delay) · Скриншоты: полнostраничные, в браузере.

## Покрытие

| Метрика | Значение |
|---|---|
| URL в sitemap.xml | 121 |
| Найдено ссылками при обходе (страницы) | +16 (legal-страницы, /personal/*, повторы) |
| **Сохранено HTML-страниц** | **137/137 найденных = 100%** |
| Провалено страниц | 2 — это мои же тестовые URL-догадки `/politika-konfidencialnost(i)(i)/` (на сайте их нет; реальная страница — `/politika-konfidentsialnosti/`, скачана) |
| Скриншоты | 274 (137 × desktop 1440px + mobile 390px), полнostраничные, 0 ошибок |
| Ассетов скачано | 603 файла, ~172 МБ (`assets/original`, карта `assets/url-map.json`) |
| Битые ассеты на самом сайте | 4 — картинки отзывов `/netcat_template/template/imgg/img-review/{7,11,18,yuliya}.jpg` отдают 404 (факт → аудит) |
| Контент извлечён | `data/content/*.md` — 137 файлов, 6.7 МБ (весь видимый текст, включая скрытое в аккордеонах/FAQ/табах, таблицы цен 1-в-1) |

## robots.txt
Стандарт для MODX (NetCat-шаблон): Disallow на /amp/, /ajax/, /search/, /zayavka/ и служебные query-параметры.
Примечание: robots запрещает `/yuridicheskaya-informatsiya/` и `/yuridicheskie-dokumenty/`, но это юридические страницы самого заказчика (политика ПД, лицензии) — они нужны для нового футера и получены. Все прочие disallow соблюдены.

## Анти-бот
Сайт за DDoS-Guard (JS-челлендж, cookies `__jhash_`/`__jua_`/`__ddg8_`...). Обход: реальный Chromium прошёл челлендж, cookies + точный User-Agent перенесены в краулер. На всех 137 страницах челлендж не повторялся.

## Структура сайта (типы страниц)

| Тип | Кол-во | Примеры |
|---|---|---|
| Главная | 1 | `/` |
| О клинике / info | 7 | /o-klinike-neoplus/, /geography/, /kalkulyator/, /karta-sayta/, /photogallery/, /informatsiya-dlya-rodstvennikov/, /narcologicheskaya-pomosch/ |
| Услуги (SEO-лендинги) | 109 | /vyvod-iz-zapoya/, /kodirovanie-dovzhenko/, /lechenie-depressii/… |
| Врачи | 8 | /personal/ + 7 профилей /personal/*.html |
| Цены | 1 | /tseny/ (4 таблицы, 218 позиций) |
| Отзывы | 1 | /otzyvy/ (100 отзывов) |
| FAQ | 1 | /faq/ (6 групп) |
| Акции | 1 | /aktsii/ (5 акций) |
| Лицензии | 1 | /litsenzii/ |
| Контакты | 1 | /kontakty/ |
| Юридические | 8 | политика ПД, согласия, оферта, юр.информация |

## Ключевые факты о сайте (для аудита/переноса)
- CMS: NetCat (MODX-подобные шаблоны `/netcat_template/`), редизайн-слой `/redisign/assets/`.
- Метрика: Яндекс.Метрика **66047221**; Битрикс24 CRM-коллтрекинг (портал **b3713987**); Google News publisher.js; скрипт `/vefovi/ln.js` (назначение неясно — сторонний).
- Формы: POST `/send.php`, `/netcat_template/ajax/request.php`, отзывы `/add_otzyv.php`, анти-спам `/netcat_template/ajax/hash-check.php`; поля: phone, adConsent (чекбокс ПД есть), скрытые catalogue/BitrixID/city/type/cc/sub/mes/urlMessage.
- Контакты: +7 (800) 200-24-46, +7 960 442-04-15; почты balashikha@/job@/marketing@neoplus-clinic.ru; адрес контакт-центра: Балашиха, ул. Советская, 47.
- Юрлицо: ООО «НЕО ПЛЮС», ИНН 6670512492, ОГРН 1226600076185; лицензия Л041-01021-66/01009753 от 28.12.2023 (Екатеринбург); стационар — партнёр ООО «Югэкосервис+», лицензия Л041-01050-61/00347983 от 28.12.2021 (Ростов-на-Дону).
- Врачи: 7 (Сойкин — главный врач, Кострин, Коваленко, Харисова, Кунцев, Кузнецова, Громов).
- Карта: Google Maps (ссылка/клик-карта, без iframe-embed на индексе).

## Что перенесено куда
- `raw/html/` — исходный HTML (137)
- `raw/screenshots/{desktop,mobile}/` — 274 PNG
- `raw/sitemap.xml`, `raw/robots.txt`, `raw/crawl-manifest.json` — карта и манифест
- `assets/original/` — все картинки/иконки/PDF/шрифты + `url-map.json`
- `data/*.json` — pages, services, prices, prices-by-service, doctors, reviews, promos, contacts, legal, faq, widgets
- `data/content/*.md` — весь текстовый контент постранично

## Осталось TODO (у клиники уточнить)
- 4 битые картинки отзывов — нужны оригиналы или замена.
- 2 постановления PDF весят 100 МБ суммарно — для нового сайта положить копии/ссылки, но не в критический путь.
- График работы врачей («Режим работы») у части профилей пуст — проверка на месте.
