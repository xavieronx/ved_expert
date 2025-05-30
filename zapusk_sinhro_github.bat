@echo off
:: Настройка имени и почты Git
git config --global user.name "Жека"
git config --global user.email "jekabot@example.com"
echo ✅ Git user.name и user.email настроены!

:: Переход в папку проекта и пуш
cd /d "C:\VED EXP\BOT_Telega_GPT\ved_expert-main"
git add .
git commit -m "🚀 Авто-коммит от Жеки"
git push
pause