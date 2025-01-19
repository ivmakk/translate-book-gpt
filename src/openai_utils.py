# Prices per million tokens
INPUT_PRICES_PER_MILLION = {
    'gpt-4o': 2.50,
    'gpt-4o-mini': 0.150,
    'o1-mini': 3.00
}

OUTPUT_PRICES_PER_MILLION = {
    'gpt-4o': 10.00,
    'gpt-4o-mini': 0.6,
    'o1-mini': 12.00
}

def calculate_price(tokens, model_name, token_type='input'):
    """Calculate the price for the given number of tokens and model.
    
    Args:
        tokens (int): The number of tokens.
        model_name (str): The name of the model.
        token_type (str): The type of tokens ('input' or 'output').

    Returns:
        float: The calculated price.
    """
    if token_type == 'input':
        model_prices_per_million = INPUT_PRICES_PER_MILLION
    elif token_type == 'output':
        model_prices_per_million = OUTPUT_PRICES_PER_MILLION
    else:
        return 0

    if model_name not in model_prices_per_million:
        return 0

    price_per_million = model_prices_per_million[model_name]
    price_per_token = price_per_million / 1_000_000

    return tokens * price_per_token