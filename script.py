# Instalar tiktoken si no está disponible:
# !pip install tiktoken

import tiktoken

# Cargar el tokenizer para gpt-4o (o200k_base)
enc = tiktoken.encoding_for_model("gpt-4o")

# Pares de consultas (Español vs Inglés)
ejemplos = [
    {
        "es": "¿Cuándo vence el pago del monotributo este mes?",
        "en": "When is the monotax payment due this month?",
    },
    {
        "es": "Hola, ¿cuál es la fecha límite para presentar el IVA?",
        "en": "Hello, what is the deadline to file VAT?",
    },
    {
        "es": "¿Hasta cuándo tengo tiempo de pagar las cargas sociales?",
        "en": "Until when do I have time to pay payroll taxes?",
    },
    {
        "es": "¿Qué papeles necesito para dar de alta a un empleado?",
        "en": "What documents do I need to register an employee?",
    },
    {
        "es": "¿Qué comprobantes tengo que mandarles para la liquidación mensual?",
        "en": "What receipts do I need to send you for the monthly settlement?",
    },
    {
        "es": "¿Cómo viene mi trámite de inscripción en AFIP?",
        "en": "How is my AFIP registration process going?",
    },
    {
        "es": "Hola, ¿pudieron presentar el balance que les mandé la semana pasada?",
        "en": "Hello, were you able to submit the balance sheet I sent last week?",
    },
    {
        "es": "¿Cómo hago para generar una factura electrónica desde el celular?",
        "en": "How do I generate an electronic invoice from my phone?",
    },
    {
        "es": "Hola, ¿me pasan el VEP para pagar el monotributo?",
        "en": "Hello, can you send me the payment voucher to pay the monotax?",
    },
]

print(f"{'Ejemplo':<4} | {'Tokens ES':<9} | {'Tokens EN':<9} | {'Diferencia (ES - EN)':<20} | {'Variación (%)'}")
print("-" * 75)

total_tokens_es = 0
total_tokens_en = 0

for i, ej in enumerate(ejemplos, 1):
    tokens_es = len(enc.encode(ej["es"]))
    tokens_en = len(enc.encode(ej["en"]))
    diff = tokens_es - tokens_en
    pct_diff = ((tokens_es - tokens_en) / tokens_en) * 100

    total_tokens_es += tokens_es
    total_tokens_en += tokens_en

    print(f"\n[{i}]")
    print(f"  ES: \"{ej['es']}\" ({tokens_es} tokens)")
    print(f"  EN: \"{ej['en']}\" ({tokens_en} tokens)")
    signo = "+" if diff > 0 else ""
    print(f"  Diferencia: {signo}{diff} tokens ({pct_diff:+.1f}%)")

print("\n" + "=" * 75)
total_diff = total_tokens_es - total_tokens_en
total_pct = (total_diff / total_tokens_en) * 100
print(f"TOTAL ES: {total_tokens_es} tokens")
print(f"TOTAL EN: {total_tokens_en} tokens")
print(f"Diferencia total: {total_diff:+d} tokens ({total_pct:+.1f}%)")
