#!/usr/bin/env python3

# -*- coding: utf-8 -*-


import sys

import os


if sys.platform == "win32":

    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


print("=" * 60)

print("🔍 ВАЛІДАЦІЯ ПРОЕКТУ")

print("=" * 60)


print("\n📦 Перевірка модулів Python:")

modules = [
    "constants",
    "base_entity",
    "game_entities",
    "maze_generator",
    "level_validator",
    "fog_of_war",
    "menu",
    "sound_manager",
    "game_manager",
    "main",
]


failed = []

for module in modules:

    try:

        __import__(module)

        print(f"  ✅ {module}")

    except Exception as e:

        print(f"  ❌ {module}: {e}")

        failed.append(module)


print("\n🎨 Перевірка спрайтів:")

sprites = [
    "sprites/player.png",
    "sprites/enemy.png",
    "sprites/artifact.png",
    "sprites/key.png",
    "sprites/exit.png",
    "sprites/trap.png",
    "sprites/door.png",
    "sprites/wall.png",
    "sprites/path.png",
]


for sprite in sprites:

    if os.path.exists(sprite):

        size = os.path.getsize(sprite)

        print(f"  ✅ {sprite} ({size} bytes)")

    else:

        print(f"  ❌ {sprite} - НЕ ЗНАЙДЕНО")

        failed.append(sprite)


print("\n📚 Перевірка документації:")

docs = ["README.md", "ARCHITECTURE.md", "QUICK_START.md"]


for doc in docs:

    if os.path.exists(doc):

        print(f"  ✅ {doc}")

    else:

        print(f"  ❌ {doc} - НЕ ЗНАЙДЕНО")


print("\n🔊 Перевірка звуків:")

sounds = [
    "sounds/menu_music.wav",
    "sounds/footstep.wav",
    "sounds/enemy_attack.wav",
    "sounds/damage.wav",
    "sounds/collect_key.wav",
    "sounds/collect_artifact.wav",
    "sounds/artifact_weapon.wav",
    "sounds/victory.wav",
    "sounds/defeat.wav",
]


for sound in sounds:

    if os.path.exists(sound):

        size = os.path.getsize(sound)

        print(f"  ✅ {sound} ({size} bytes)")

    else:

        print(f"  ❌ {sound} - НЕ ЗНАЙДЕНО")

        failed.append(sound)


print("\n" + "=" * 60)

if not failed:

    print("✅ ВСЕ ПЕРЕВІРКИ ПРОЙДЕНІ!")

    print("=" * 60)

    print("\n🎮 Проект готовий до демонстрації.")

    print("\n⚡ Запуск: python main.py")

    sys.exit(0)

else:

    print(f"❌ ВИЯВЛЕНО {len(failed)} ПОМИЛОК:")

    for f in failed:

        print(f"  - {f}")

    print("=" * 60)

    sys.exit(1)
