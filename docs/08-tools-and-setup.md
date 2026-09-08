# 08 — Инструменти и настройка

## Машина

MacBook Pro M1 Pro, 32 GB — достатъчна за Blender, скан обработка, големи STL.

## Софтуер (без абонаменти)

| Инструмент | За какво | Статус |
|---|---|---|
| Blender 5.2 | Всичко surfacing; subdivision modelling върху референции | инсталиран |
| Blender MCP (ahujasid/blender-mcp) | Claude управлява Blender: клетка, импорт/мащаб, измервания, clearance, разрязване, експорт | addon инсталиран, порт 9876, telemetry OFF |
| uv / uvx | Стартира MCP сървъра | инсталиран (brew) |
| Claude Desktop | Чат + Blender MCP за интерактивна работа | конфигурира се |
| Claude Code | Repo, скриптове, git, Blender MCP за скриптовата фаза | следваща стъпка |
| Plasticity (€99–299 еднократно) | NURBS: дебелина, фланци, разрязване — ако Blender стане болезнен | по-късно, при нужда |
| Revo Scan | Скенерът | при покупка на скенера |
| Fusion 360 | Не е нужен за този workflow | — |

## Blender MCP — Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"]
    }
  }
}
```

Ако Claude Desktop не намира uvx (`spawn uvx ENOENT`): `which uvx` в
терминала и сложи пълния път (обикновено `/opt/homebrew/bin/uvx`).
В Blender: N → таб "MCP for Blender" → Connect to MCP server (порт 9876).
Blender трябва да е отворен преди старта на Claude.

## Claude Code — инсталация и закачане към репото

```bash
# инсталация (native, без Node)
curl -fsSL https://claude.ai/install.sh | bash
claude --version
claude doctor

# в папката на репото
cd ~/path/to/vehicle-3d-modeling
claude            # първи старт → /login с claude.ai акаунта

# Blender MCP за Claude Code (Blender отворен, сървърът стартиран)
claude mcp add blender -- uvx blender-mcp
claude mcp list   # blender трябва да е с отметка
```

Claude Code чете `CLAUDE.md` автоматично при всяка сесия. Референтните
картинки в `07_PRESENTATION/references/` се четат с "отвори ref-05" — Claude
Code вижда изображения от файловата система.

Алтернатива без терминал: Claude Desktop → таб Code → отваряш папката на
репото; същото поведение.

## Git конвенции

- Commit при всеки завършен етап (`fender v3 — arch line fixed`).
- `.blend1`/`.blend2` бекъпи, `__pycache__`, временни експорти — в `.gitignore`.
- Големи STL (>50 MB) — Git LFS или извън репото с линк.
- Клетката винаги се регенерира от `01_CAD/scripts/cage_986.py`, никога не се
  редактира ръчно.

## Учебен път в Blender (само това, което трябва)

1. Навигация, модификатори, Subdivision Surface, Mirror, Shrinkwrap (за
   snap към скан/подложка).
2. Reference Images в трите равнини, мащабиране по междуосието.
3. Subdivision modelling на калник върху подложка — търси "Blender car
   modeling tutorial" (CG Fast Track, Blender Guru за основи).
4. Solidify, Boolean, разрязване за печат, експорт STL/3MF.
