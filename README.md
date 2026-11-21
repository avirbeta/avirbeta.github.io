# avirbeta.github.io

Личный сайт-визитка **avirbeta** — разработчика Minecraft-модов, Java/Go и веб-проектов.

**Сайт:** https://avirbeta.github.io/

## Что внутри

- одностраничный статический сайт: HTML + CSS + JavaScript, без сборки;
- тёмная неоновая тема с настройкой цветов;
- переключение языка RU/EN;
- таймер до дня рождения;
- живые проекты из GitHub API с кэшем на 24 часа;
- адаптивная вёрстка, мобильное меню, кнопка «наверх».

## Локальный просмотр

```bash
python3 -m http.server 8080
```

Открой http://127.0.0.1:8080/

## Проверка

```bash
python3 scripts/check_site.py
```

Скрипт проверяет:

- обязательные мета-теги (description, Open Graph, Twitter, canonical);
- валидный JSON-LD;
- уникальность `id` и целостность якорных ссылок;
- `alt` у картинок и `rel="noopener"` у внешних ссылок;
- парность переводов `data-ru` / `data-en`;
- наличие файлов сайта;
- синтаксис inline-JavaScript через `node --check`.

Те же проверки запускаются в GitHub Actions при каждом push и pull request.

## Деплой

Сайт раздаётся через **GitHub Pages** из ветки `main`: любой push автоматически
публикует новую версию на https://avirbeta.github.io/.

## Структура

```
index.html          — вся страница (HTML + CSS + JS)
ава.webp            — аватар
og-image.jpg        — превью для соцсетей
robots.txt          — правила индексации
sitemap.xml         — карта сайта
scripts/check_site.py — проверки сайта
```

## Лицензия

[MIT](LICENSE)
