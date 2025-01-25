# Translate books with LLM (OpenAI, Anthropic, Gemini)

![Supported Python Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)


> ⚠️ **Disclaimer:** This project is intended for personal use only. Ensure you have the right to translate and use the eBooks you process with this tool. Unauthorized use of copyrighted material is illegal and strictly prohibited. 
> 
> This fork of the [original project](https://github.com/jb41/translate-book) does not maintain backward compatibility, as it focuses on developing new features primarily oriented towards the EPUB format.

This project harnesses the power of LLMs (OpenAI, Anthropic, Gemini, DeepSeek) to translate eBooks from any language into your preferred language, maintaining the integrity and structure of the original content. Imagine having access to a vast world of literature, regardless of the original language, right at your fingertips.

This tool not only translates the text but also carefully compiles each element of the eBook – chapters, footnotes, and all – into a perfectly formatted EPUB file. Currently supported OpenAI and Anthropic models on both require API keys. However, we understand the need for flexibility, so we've made it easy to switch models in `main.py` according to your specific needs.


## Requirements

- Python 3.8 or higher
- pip (Python package installer)

Note: While the code may work with Python 3.7, we recommend Python 3.8+ for best compatibility with all dependencies and to ensure proper type hint support.


## 🛠️ Installation

To install the necessary components for our project, follow these simple steps:

```bash
pip install -r requirements.txt
cp .env.example .env
```

Remember to add your API key(s) to `.env`.


## 🎮 Usage

Our script comes with a variety of parameters to suit your needs. Here's how you can make the most out of it:

### Show Chapters

Before diving into translation, it's recommended to use the `show-chapters` mode to review the structure of your book:

```bash
python main.py show-chapters --input yourbook.epub
```

This command will display all the chapters, helping you to plan your translation process effectively.

### Translate Mode

#### Basic Usage

To translate a book from English to Polish, use the following command:

```bash
python main.py translate --input yourbook.epub --output translatedbook.epub  --from-lang EN --to-lang PL
```

#### Advanced Usage

For more specific needs, such as translating from chapter 13 to chapter 37 from English to Polish, use:

```bash
python main.py translate --input yourbook.epub --output translatedbook.epub --from-chapter 13 --to-chapter 37 --from-lang EN --to-lang PL
```


## 📚 Configuration

All configuration values are defined as environment variables and can be stored in `.env` file.

- `MODEL_VENDOR`: The AI model provider
  - Supported values: `openai`, `anthropic`, `google`, `deepseek`
  - Default: `openai`

- `MODEL_NAME`: Name of the model to use
  - Supported values:
    - For OpenAI : `gpt-4o`, `gpt-4o-mini`, `o1-mini` (see [full list](https://platform.openai.com/docs/models))
    - For Anthropic : `claude-2`, `claude-instant-1` (see [full list](https://docs.anthropic.com/en/docs/about-claude/models))
    - For Gemini : `gemini-1.5-pro`, `gemini-1.5-flash`, `gemini-2.0-flash-exp` (see [full list](https://ai.google.dev/gemini-api/docs/models/gemini))
    - For DeepSeek : `deepseek-chat` (see [full list](https://api-docs.deepseek.com/quick_start/pricing))
  - Default: `gpt-4o-mini`

- `TEMPERATURE`: Controls randomness in model responses. Lower values are more focused/deterministic
  - Supported values: `0.0` to `1.0`
  - Default: `0.2`

- `OPENAI_API_KEY`: Your OpenAI API key. Required when using OpenAI models.

- `ANTHROPIC_API_KEY`: Your Anthropic API key. Required when using Anthropic models.

- `GEMINI_API_KEY`: Your Gemini API key. Required when using Gemini models.

- `DEEPSEEK_API_KEY`: Your DeepSeek API key. Required when using DeepSeek models.

### Translation Tunning

- `MAX_CHUNK_SIZE`: Maximum size of the chunk to translate. Adjust this based on max output tokens of the model (e.g. for Anthropic models with 4096 tokens limit, set chunk size to ~5000).
  - Default: `10_000` 

## Models Differences

### Tokens Usage
Each model has different token usage, token input/output limits and pricing.

For example, the same content translated by `gpt-4o-mini` and `claude-3-haiku-20240307` shows different token usage:

| Model | Input Tokens | Output Tokens | Total Tokens |
|-------|--------------|---------------|--------------|
| gpt-4o-mini | 1,101 | 1,160 | 2,261 |
| gpt-4o | 1,101 | 1,172 | 2,273 |
| claude-3-haiku-20240307 | 1,437 | 1,546 | 2,983 |

To accommodate model token limits, adjust the `max_chunk_size` parameter in splitter functions. For example, setting `max_chunk_size=5000` ensures chunks fit within the 4,096 token limit of `claude-3-haiku-20240307` for Cyrillic target languages. This helps prevent truncation while maintaining translation quality.

## Converting from AZW3 to EPUB

For books in AZW3 format (Amazon Kindle), use Calibre (https://calibre-ebook.com) to convert them to EPUB before using this tool.


## DRM (Digital Rights Management)

Amazon eBooks (AZW3 format) are encrypted with your device's serial number. To decrypt these books, use the DeDRM tool (https://dedrm.com). You can find your Kindle's serial number at https://www.amazon.com/hz/mycd/digital-console/alldevices.


## 🤝 Contributing

We warmly welcome contributions to this project! Your insights and improvements are invaluable. Currently, we're particularly interested in contributions in the following areas:

- Support for other eBook formats: AZW3, MOBI, PDF.
- Integration of a built-in DeDRM tool

Join us in breaking down language barriers in literature and enhancing the accessibility of eBooks worldwide!
