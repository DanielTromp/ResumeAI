"""
Resume Processing Module

Dit script verwerkt CV's en vacatures door:
1. Het ophalen van nieuwe vacatures uit Airtable
2. Het vergelijken van CV's met vacatures via embeddings
3. Het evalueren van matches met behulp van GPT-4
4. Het bijwerken van de vacaturestatus in Airtable

Het script maakt gebruik van:
- OpenAI's API voor embeddings en GPT-4 evaluaties
- Supabase voor vector similarity search
- Airtable voor vacature- en CV-beheer

Author: Daniel Tromp
Version: 1.0.0
Created: 2024-02-14
License: MIT
"""

import os
import json
from collections import defaultdict
from dotenv import load_dotenv
from openai import OpenAI
import supabase
from pyairtable import Api
import tiktoken

# Omgevingsvariabelen laden
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME_AANVRAGEN = os.getenv("AIRTABLE_TABLE_NAME_AANVRAGEN")
AIRTABLE_TABLE_NAME_EXCLUDED = os.getenv("AIRTABLE_TABLE_NAME_EXCLUDED")
OPENROUTESERVICE_KEY = os.getenv("OPENROUTESERVICE")

# Verbinding maken met services
api = Api(AIRTABLE_API_KEY)
vacatures_table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_AANVRAGEN)
excluded_clients_table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME_EXCLUDED)
client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
client_openai = OpenAI(api_key=OPENAI_API_KEY)

# Token calculator initialiseren
enc = tiktoken.encoding_for_model("gpt-4")

def get_excluded_clients():
    """Haalt lijst van uitgesloten klanten op uit Airtable."""
    records = excluded_clients_table.all()
    return {record['fields'].get('Klant', '').strip() for record in records if 'Klant' in record['fields']}

def count_tokens(text: str) -> int:
    """Telt het aantal tokens in een tekst."""
    return len(enc.encode(text))

def get_embedding(text: str) -> list[float]:
    """Genereert een embedding voor de gegeven tekst met behulp van OpenAI's API."""
    embedding_response = client_openai.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return embedding_response.data[0].embedding

def evaluate_candidate(naam: str, cv_text: str, vacature_text: str) -> tuple[dict, dict]:
    """Evalueert een kandidaat en returnt een JSON-gestructureerd resultaat en token counts.
    
    Args:
        naam: De naam van de kandidaat
        cv_text: De tekst van het CV van de kandidaat
        vacature_text: De tekst van de vacature
    
    Returns:
        Een tuple met een dictionary van de evaluatie en een dictionary van token counts
    """
    prompt = (
        "Evalueer de geschiktheid van een kandidaat voor een specifieke vacature op basis van de opgegeven functiebeschrijving en CV.\n\n"
        "**Functieomschrijving:**\n"
        f"{vacature_text}\n\n"
        "**Gewenste kwalificaties en vaardigheden:**\n"
        "- Vereiste vaardigheden worden uit de functieomschrijving gehaald\n"
        "- Optionele vaardigheden worden uit de functieomschrijving gehaald\n"
        "- Ervaring in relevante sector wordt uit de functieomschrijving gehaald\n"
        "- Vermogen om specifieke taken uit te voeren wordt uit de functieomschrijving gehaald\n"
        "- Eventuele extra eisen worden uit de functieomschrijving gehaald\n\n"
        "**Kandidaatgegevens (CV):**\n"
        f"- Naam: {naam}\n"
        f"- CV tekst: {cv_text}\n\n"
        "### **Beoordelingscriteria:**\n"
        "1. **Functieniveau vergelijking (ZEER BELANGRIJK):** \n"
        "   - Vergelijk het niveau van de huidige functie met de vacature\n"
        "   - Een stap terug in functieniveau is NIET wenselijk\n"
        "   - Geef een negatief advies als de vacature een duidelijke stap terug is\n"
        "   - Weeg dit zwaar mee in het matchpercentage\n"
        "2. **Relevantie van werkervaring:** Hoe goed sluit de werkervaring van de kandidaat aan bij de functie? "
        "Is de ervaring **strategisch, operationeel of hands-on**?\n"
        "3. **Vaardigheden match:** Heeft de kandidaat de vereiste vaardigheden en hoe sterk zijn ze aanwezig?\n"
        "4. **Praktische inzetbaarheid:** Is de kandidaat direct inzetbaar of is er een leercurve?\n"
        "5. **Risico's:** Zijn er risico's door gebrek aan specifieke ervaring, werkstijl of een te groot verschil met de functie?\n\n"
        "### **Uitvoer:**\n"
        "- **Matchpercentage (0-100%)** op basis van hoe goed de kandidaat past bij de functie.\n"
        "  Als de vacature een stap terug is in functieniveau, geef dan maximaal 40% match.\n"
        "- **Sterke punten** van de kandidaat.\n"
        "- **Zwakke punten** en aandachtspunten.\n"
        "- **Eindoordeel** of de kandidaat geschikt is, met argumentatie.\n"
        "  Begin het eindoordeel met een duidelijke analyse van het functieniveau verschil.\n\n"
        "Geef je antwoord in JSON formaat met de volgende velden: naam, percentage, sterke_punten, zwakke_punten, eindoordeel"
    )

    # Tel input tokens
    prompt_tokens = count_tokens(prompt)
    system_tokens = count_tokens(
        "Je bent een ervaren HR-specialist. Geef alleen JSON output terug. "
        "Als het percentage <60% is, geef een korte onderbouwing waarom de match laag is. "
        "Als het percentage >=60% is, geef een uitgebreide onderbouwing met prioriteiten "
        "per verbeterpunt, waarbij je percentages toevoegt die exact optellen tot (100% - het matchpercentage)."
    )
    
    response = client_openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "Je bent een ervaren HR-specialist. Geef alleen JSON output terug. "
                "Als het percentage <60% is, geef een korte onderbouwing waarom de match laag is. "
                "Als het percentage >=60% is, geef een uitgebreide onderbouwing met prioriteiten "
                "per verbeterpunt, waarbij je percentages toevoegt die exact optellen tot (100% - het matchpercentage)."
            )},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )

    # Tel output tokens
    output_tokens = count_tokens(response.choices[0].message.content)
    
    token_counts = {
        "input_tokens": prompt_tokens + system_tokens,
        "output_tokens": output_tokens,
        "total_tokens": prompt_tokens + system_tokens + output_tokens
    }

    try:
        return json.loads(response.choices[0].message.content), token_counts
    except json.JSONDecodeError:
        return {
            "naam": naam,
            "percentage": 0,
            "sterke_punten": [],
            "zwakke_punten": [],
            "eindoordeel": "Error: Kon geen valide JSON-response genereren"
        }, token_counts

def process_vacancy(vacancy_id: str, vacancy_text: str, matches: dict) -> tuple[dict, dict]:
    """Verwerkt één vacature en evalueert alle kandidaten."""
    print(f"\n📊 Start evaluatie van {len(matches)} kandidaten voor vacature {vacancy_id}")
    
    all_evaluations = []
    token_usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "evaluations_count": 0
    }
    
    for naam, chunks in matches.items():
        print(f"  👤 Evalueren van kandidaat: {naam}")
        cv_text = " ".join(chunks)
        evaluation, tokens = evaluate_candidate(naam, cv_text, vacancy_text)
        all_evaluations.append(evaluation)
        
        # Update token statistieken
        token_usage["input_tokens"] += tokens["input_tokens"]
        token_usage["output_tokens"] += tokens["output_tokens"]
        token_usage["total_tokens"] += tokens["total_tokens"]
        token_usage["evaluations_count"] += 1
        
        print(f"    ✓ Match percentage: {evaluation['percentage']}%")
        print(f"    📈 Tokens: input={tokens['input_tokens']}, output={tokens['output_tokens']}, totaal={tokens['total_tokens']}")

    # Sorteer evaluaties op percentage (hoogste eerst)
    sorted_evaluations = sorted(
        all_evaluations,
        key=lambda x: x["percentage"],
        reverse=True
    )

    # Neem de top 5 kandidaten
    top_evaluations = sorted_evaluations[:5]
    best_match = top_evaluations[0] if top_evaluations else None
    
    if best_match:
        # Bepaal nieuwe status gebaseerd op match percentage
        new_status = "Open" if best_match["percentage"] >= 60 else "AI afgewezen"
        
        return {
            "Checked_resumes": ", ".join(eval["naam"] for eval in top_evaluations),
            "Top_Match": best_match["percentage"] / 100,
            "Match Toelichting": json.dumps({
                "beste_match": best_match,
                "alle_matches": top_evaluations,
                "token_usage": token_usage
            }, ensure_ascii=False, indent=2),
            "Status": new_status
        }, token_usage
    return None, token_usage

def main():
    # Haal uitgesloten klanten op
    excluded_clients = get_excluded_clients()
    print(f"ℹ️ Geladen uitgesloten klanten: {len(excluded_clients)}")

    # Ophalen van vacatures met status "Nieuw"
    vacancies = vacatures_table.all(formula="Status='Nieuw'")
    if not vacancies:
        print("❌ Geen nieuwe vacatures gevonden in Airtable.")
        return

    print(f"📄 Gevonden {len(vacancies)} nieuwe vacatures.")
    
    total_token_usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "total_evaluations": 0
    }

    for vacancy in vacancies:
        vacature_id = vacancy["id"]
        vacature_data = vacancy["fields"]
        klant = vacature_data.get("Klant", "").strip()
        
        # Check of klant is uitgesloten
        if klant in excluded_clients:
            print(f"⏭️ Klant '{klant}' staat in de uitsluitingslijst, markeren als AI afgewezen")
            vacatures_table.update(vacature_id, {"Status": "AI afgewezen"})
            continue

        vacature_tekst = vacature_data.get("Functieomschrijving", "")
        if not vacature_tekst:
            print(f"⚠️ Geen functieomschrijving gevonden voor vacature {vacature_id}, overslaan.")
            continue

        print(f"\n🔍 Verwerken van vacature: {vacature_data.get('Functie', 'Onbekend')} ({vacature_id})")

        # Vector search uitvoeren via de RPC-functie voor table "01_OAS"
        vacature_embedding = get_embedding(vacature_tekst)
        query = client.rpc("match_01_oas", {
            "query_embedding": vacature_embedding,
            "match_threshold": 0.75,
            "match_count": 20
        }).execute()

        if not query.data:
            print(f"⚠️ Geen matches gevonden voor vacature {vacature_id}")
            vacatures_table.update(vacature_id, {"Status": "AI afgewezen"})
            continue

        # Resultaten groeperen per kandidaat
        matches = defaultdict(list)
        for item in query.data:
            matches[item["naam"]].append(item["cv_chunk"])

        print(f"📝 Gevonden {len(matches)} unieke kandidaten voor evaluatie")

        # Verwerk de vacature en krijg de resultaten
        results, vacancy_tokens = process_vacancy(vacature_id, vacature_tekst, matches)
        
        total_token_usage["input_tokens"] += vacancy_tokens["input_tokens"]
        total_token_usage["output_tokens"] += vacancy_tokens["output_tokens"]
        total_token_usage["total_tokens"] += vacancy_tokens["total_tokens"]
        total_token_usage["total_evaluations"] += vacancy_tokens["evaluations_count"]
        
        if results:
            print(f"📝 Bijwerken van vacature {vacature_id} met resultaten")
            vacatures_table.update(vacature_id, results)
            print(f"✅ Vacature {vacature_id} succesvol verwerkt")
            print(f"📊 Token gebruik voor deze vacature: input={vacancy_tokens['input_tokens']}, "
                  f"output={vacancy_tokens['output_tokens']}, totaal={vacancy_tokens['total_tokens']}")
        else:
            print(f"⚠️ Geen resultaten gegenereerd voor vacature {vacature_id}")
            vacatures_table.update(vacature_id, {"Status": "AI afgewezen"})

    print("\n📈 Eindrapport token gebruik:")
    print(f"Totaal input tokens: {total_token_usage['input_tokens']}")
    print(f"Totaal output tokens: {total_token_usage['output_tokens']}")
    print(f"Totaal aantal tokens: {total_token_usage['total_tokens']}")
    print(f"Totaal aantal evaluaties: {total_token_usage['total_evaluations']}")
    if total_token_usage['total_evaluations'] > 0:
        avg_tokens = total_token_usage['total_tokens'] / total_token_usage['total_evaluations']
        print(f"Gemiddeld aantal tokens per evaluatie: {avg_tokens:.2f}")
    
    print("\n🚀 Alle vacatures succesvol verwerkt!")

if __name__ == "__main__":
    main()