# Балашихинский наркологический центр — новый сайт клиники

Полная пересборка сайта `balashikha.neoplus-clinic.ru` под брендом **«Балашихинский наркологический центр»** (прежнее имя «Нео+» сохранено как alternateName в schema.org и в цитатах пациентов): сбор 100% контента со старого сайта → аудит → дизайн-система → статический сайт на **Astro 5 + Tailwind CSS 4 + TypeScript**.

## Структура репозитория

```
/data           — структурированный JSON: pages, services, prices, prices-by-service, doctors, reviews,
                  promos, contacts, legal, faq, widgets + build/ (данные для сборки) + content/ (137 md-файлов со всем текстом)
/site           — исходники нового сайта (Astro)
/dist           — собранный статический сайт (копия site/dist)
crawl-report.md — отчёт о сборе (100% покрытие)
audit.md        — аудит старого сайта
design-system.md— дизайн-система
redirects.csv   — редиректы склеенных дублей
nginx-redirects.conf, .htaccess — конфиги редиректов
todo.md         — что осталось решить/уточнить
assets-credits.md — источники изображений
```

Локально (в .gitignore, вне репозитория): `/raw` (сырой HTML старого сайта, 274 скриншота),
`/assets` (оригиналы файлов старого сайта), `/qa` (скриншоты нового сайта + Lighthouse-отчёты),
`/logs`.

Живое превью собранного сайта: **https://ushure.github.io/** (репозиторий `ushure.github.io`, содержимое `/dist`).

## Запуск

```bash
cd site
npm install
npm run dev        # dev-сервер на localhost:4321
npm run build      # сборка в site/dist
npm run preview    # предпросмотр собранного
```

После `npm run build` выполните `python3 scripts/postbuild.py` из корня проекта — он:
1. Превращает страницы врачей `personal/<name>.html/index.html` в файлы `personal/<name>.html` (сохранение старых URL);
2. Генерирует `robots.txt` и `sitemap.xml` (135 URL);
3. Копирует сборку в корневой `/dist`.

## Как править контент (без кода)

Все тексты и данные — в JSON, код их только рендерит:

| Что | Файл | Заметки |
|---|---|---|
| Цены (весь прайс) | `data/prices.json` + `data/prices-by-service.json` | После правки: `python3 scripts/prep_build_data.py` не нужен — правьте сразу `site/src/data/*.json`, затем `npm run build` |
| Услуги (тексты, цены, FAQ) | `site/src/data/service-pages.json` | Один элемент = одна страница; URL менять осторожно (301!) |
| Врачи | `site/src/data/doctors.json` | имя/специальность/фото/образование/график |
| Отзывы | `site/src/data/reviews.json` | только реальные отзывы |
| Акции | `site/src/data/promos.json` | |
| Контакты/юрлицо | `site/src/data/contacts.json` | |
| Юридич. страницы | `site/src/data/legal-pages.json` | |
| Фото | `site/public/img/` | heroes/, doctors/, gallery/, licenses/, reviews/ |

## Деплой

1. Загрузить содержимое `/dist` на хостинг (любой статический: nginx, S3+CDN, Netlify).
2. Подключить редиректы из `nginx-redirects.conf` (или `.htaccess` для Apache).
3. Настроить обработку форм: фронт шлёт POST на `/send.php` (как на старом сайте) — нужен серверный обработчик
   (старый NetCat-endpoint или свой прокси на Битрикс24). Поля формы не изменились
   (`catalogue=497`, `BitrixID=UC_6KMDMY`, `city=Балашиха`, `params[phone][]`, `params[adConsent][]`).
4. DNS/SSL как у текущего поддомена.

## Перенесённая аналитика

- **Яндекс.Метрика №66047221** — подключена на каждой странице (загружается после первого взаимодействия посетителя
  или через 5 с, чтобы не блокировать рендер; счётчик срабатывает как обычно).
- **Битрикс24-коллтрекинг** (`cdn-ru.bitrix24.ru/b3713987/crm/tag/call.tracker.js`) — НЕ подключён автоматически:
  скрипт требует активного виджета Битрикс24; включите его в `site/src/layouts/Base.astro` рядом с Метрикой при необходимости.

## Качество (проверено 11.11.2026)

- Lighthouse mobile (5 ключевых страниц): Performance 99–100, Accessibility 95–97, Best Practices 100, SEO 100.
- Битые внутренние ссылки: 0 (проверка по всем 138 страницам dist).
- 301: склеенные дубли `/narkologicheskij-dispanser/` и `/reabilitatsiya-narkozavisimykh/` — в redirects.csv,
  обе страницы при этом существуют с canonical на основную (100% перенос URL).
- schema.org: MedicalClinic (все страницы), BreadcrumbList, MedicalProcedure+Offer (услуги), Physician (врачи),
  FAQPage (FAQ и услуги). Review/AggregateRating не ставились — на старом сайте нет дат и верифицируемых рейтингов
  (требование «только реальные»).
- Дисклеймер «Имеются противопоказания…» на всех страницах услуг и промо-блоках; формы — с чекбоксом согласия
  на ПД (152-ФЗ) и cookie-баннером.

## Правовые моменты

- Юрлицо/лицензии в футере: ООО «НЕО ПЛЮС», ИНН 6670512492, ОГРН 1226600076185, лицензия Л041-01021-66/01009753;
  стационар — партнёр ООО «Югэкосервис+» (лицензия Л041-01050-61/00347983). Адрес услуг — Екатеринбург (как на старом сайте).
- `/yuridicheskaya-informatsiya/` и `/yuridicheskie-dokumenty/` закрыты в robots.txt (как на старом сайте), сами страницы существуют.
- Никаких «гарантий результата» в текстах нет; формулировки из старого сайта перенесены с редактурой, факты не менялись.
