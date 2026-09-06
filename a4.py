import tiktoken

enc = tiktoken.encoding_for_model("gpt-4o")
consulta_es = "Hola estudio, quería consultarles cuáles son los deducibles que aplican para un soltero que trabaja en relación de dependencia."   # su consulta típica
consulta_en = "Hello study, I would like to inquire about the deductible options available for a single person working in an employment relationship."   # la misma traducida
print(f"ES: {len(enc.encode(consulta_es))} tokens")
print(f"EN: {len(enc.encode(consulta_en))} tokens")
