# Krea AI Style Training & Inference

## Setup

Copy `.env` and fill in your values:

```
KREA_API_KEY=...
STYLE_ID=lsmepfad3        # alinor
STYLE_NAME=alinor
PROMPT=beautiful woman
NEGATIVE_PROMPT=
STYLE_STRENGTH=0.8
ASPECT_RATIO=9:16
TRAIN_MODEL=qwen
GENERATE_MODEL=qwen
MAX_TRAIN_STEPS=500
TRAIN_TYPE=Character      # Style | Character | Object
```

## Commands

| Command | Description |
|---|---|
| `make image` | Generate an image using `STYLE_ID` |
| `make train` | Train a new style from `training_images/` |
| `make get-styles` | List all styles on your account |
| `make find-unsafe` | Find which training image Krea flags as unsafe |
| `make clean` | Remove containers and output images |

## Training

1. Put images in `training_images/`
2. Set `STYLE_NAME` in `.env`
3. Run `make train`
4. Copy the printed `STYLE_ID` into `.env`

Uploaded URLs are cached in `uploaded_urls.json` — images are not re-uploaded on retry.

## Styles

| ID | Name |
|---|---|
| `lsmepfad3` | alinor |
| `org4er6a1` | Maelis |

## Output

Generated images are saved to `output/<style_id>_<timestamp>.png`.
