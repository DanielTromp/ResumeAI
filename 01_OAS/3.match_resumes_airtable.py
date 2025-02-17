"""
Resume Processing Module

This script processes resumes and vacancies by:
1. Fetching new vacancies from Airtable
2. Comparing resumes with vacancies using embeddings
3. Evaluating matches using GPT-4o-mini
4. Updating the vacancy status in Airtable

The script uses:
- OpenAI's API for embeddings and GPT-4 evaluations
- Supabase for vector similarity search
- Airtable for vacancy and resume management

Author: Daniel Tromp
Version: 1.0.0
Created: 2024-02-14
License: MIT
"""

# Standard library imports
import os
import json
from collections import defaultdict

# Third-party imports
from openai import OpenAI
import supabase
from pyairtable import Api
import tiktoken

# Project specific imports
from config import *


# Connect to services
api = Api(AIRTABLE_API_KEY)
vacatures_table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE1)
excluded_clients_table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE2)
client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
client_openai = OpenAI(api_key=OPENAI_API_KEY)

# Initialize token calculator
enc = tiktoken.encoding_for_model("gpt-4o-mini")

def get_excluded_clients():
    """Get list of excluded clients from Airtable."""
    records = excluded_clients_table.all()
    return {record['fields'].get('Klant', '').strip() for record in records if 'Klant' in record['fields']}

def count_tokens(text: str) -> int:
    """Count the number of tokens in a text."""
    return len(enc.encode(text))

def get_embedding(text: str) -> list[float]:
    """Generate an embedding for the given text using OpenAI's API."""
    embedding_response = client_openai.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return embedding_response.data[0].embedding

def evaluate_candidate(name: str, cv_text: str, vacature_text: str) -> tuple[dict, dict]:
    """Evaluates a candidate and returns a JSON-structured result and token counts.
    
    Args:
        name: The name of the candidate
        cv_text: The text of the candidate's CV
        vacature_text: The text of the vacancy
    
    Returns:
        A tuple with a dictionary of the evaluation and a dictionary of token counts
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
        f"- name: {name}\n"
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
        "Geef je antwoord in JSON formaat met de volgende velden: name, percentage, sterke_punten, zwakke_punten, eindoordeel"
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
            "name": name,
            "percentage": 0,
            "sterke_punten": [],
            "zwakke_punten": [],
            "eindoordeel": "Error: Kon geen valide JSON-response genereren"
        }, token_counts

def process_vacancy(vacancy_id: str, vacancy_text: str, matches: dict) -> tuple[dict, dict]:
    """Processes one vacancy and evaluates all candidates."""
    print(f"\n📊 Start evaluation of {len(matches)} candidates for vacancy {vacancy_id}")
    
    all_evaluations = []
    token_usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "evaluations_count": 0
    }
    
    for name, chunks in matches.items():
        print(f"  👤 Evalueren van kandidaat: {name}")
        cv_text = " ".join(chunks)
        evaluation, tokens = evaluate_candidate(name, cv_text, vacancy_text)
        all_evaluations.append(evaluation)
        
        # Update token statistics
        token_usage["input_tokens"] += tokens["input_tokens"]
        token_usage["output_tokens"] += tokens["output_tokens"]
        token_usage["total_tokens"] += tokens["total_tokens"]
        token_usage["evaluations_count"] += 1
        
        print(f"    ✓ Match percentage: {evaluation['percentage']}%")
        print(f"    📈 Tokens: input={tokens['input_tokens']}, output={tokens['output_tokens']}, totaal={tokens['total_tokens']}")

    # Sort evaluations by percentage (highest first)
    sorted_evaluations = sorted(
        all_evaluations,
        key=lambda x: x["percentage"],
        reverse=True
    )

    # Take the top 5 candidates
    top_evaluations = sorted_evaluations[:5]
    best_match = top_evaluations[0] if top_evaluations else None
    
    if best_match:
        # Determine new status based on match percentage
        new_status = "Open" if best_match["percentage"] >= 60 else "AI afgewezen"
        
        return {
            "Checked_resumes": ", ".join(eval["name"] for eval in top_evaluations),
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
    # Get excluded clients
    excluded_clients = get_excluded_clients()
    print(f"ℹ️ Loaded excluded clients: {len(excluded_clients)}")

    # Get vacancies with status "New"
    vacancies = vacatures_table.all(formula="Status='Nieuw'")
    if not vacancies:
        print("❌ No new vacancies found in Airtable.")
        return

    print(f"📄 Found {len(vacancies)} new vacancies.")
    
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
        
        # Check if client is excluded
        if klant in excluded_clients:
            print(f"⏭️ Client '{klant}' is in the exclusion list, marking as AI afgewezen")
            vacatures_table.update(vacature_id, {"Status": "AI afgewezen"})
            continue

        vacature_tekst = vacature_data.get("Functieomschrijving", "")
        if not vacature_tekst:
            print(f"⚠️ No function description found for vacancy {vacature_id}, skipping.")
            continue

        print(f"\n🔍 Processing vacancy: {vacature_data.get('Functie', 'Unknown')} ({vacature_id})")

        # Perform vector search via the RPC function
        vacature_embedding = get_embedding(vacature_tekst)
        #print(vacature_tekst)
        
        # Debug print voor de RPC functie naam
        print(f"Using RPC function: {RESUME_RPC_FUNCTION_NAME}")
        
        try:
            # Parameters in exacte volgorde doorgeven
            query = client.rpc(
                RESUME_RPC_FUNCTION_NAME,
                {
                    "query_embedding": vacature_embedding,
                    "match_threshold": MATCH_THRESHOLD,
                    "match_count": MATCH_COUNT
                }
            ).execute()

            if not query.data:
                print(f"⚠️ No matches found for vacancy {vacature_id}")
                vacatures_table.update(vacature_id, {"Status": "AI afgewezen"})
                continue

            # Group results by candidate
            matches = defaultdict(list)
            for item in query.data:
                matches[item["name"]].append(item["cv_chunk"])

            print(f"📝 Found {len(matches)} unique candidates for evaluation")

            # Process the vacancy and get the results
            results, vacancy_tokens = process_vacancy(vacature_id, vacature_tekst, matches)
            
            total_token_usage["input_tokens"] += vacancy_tokens["input_tokens"]
            total_token_usage["output_tokens"] += vacancy_tokens["output_tokens"]
            total_token_usage["total_tokens"] += vacancy_tokens["total_tokens"]
            total_token_usage["total_evaluations"] += vacancy_tokens["evaluations_count"]
            
            if results:
                print(f"📝 Updating vacancy {vacature_id} with results")
                vacatures_table.update(vacature_id, results)
                print(f"✅ Vacancy {vacature_id} successfully processed")
                print(f"📊 Token usage for this vacancy: input={vacancy_tokens['input_tokens']}, "
                      f"output={vacancy_tokens['output_tokens']}, total={vacancy_tokens['total_tokens']}")
            else:
                print(f"⚠️ No results generated for vacancy {vacature_id}")
                vacatures_table.update(vacature_id, {"Status": "AI afgewezen"})

        except Exception as e:
            print(f"⚠️ Error processing vacancy {vacature_id}: {e}")
            vacatures_table.update(vacature_id, {"Status": "AI afgewezen"})

    print("\n📈 End report token usage:")
    print(f"Total input tokens: {total_token_usage['input_tokens']}")
    print(f"Total output tokens: {total_token_usage['output_tokens']}")
    print(f"Total number of tokens: {total_token_usage['total_tokens']}")
    print(f"Total number of evaluations: {total_token_usage['total_evaluations']}")
    if total_token_usage['total_evaluations'] > 0:
        avg_tokens = total_token_usage['total_tokens'] / total_token_usage['total_evaluations']
        print(f"Average number of tokens per evaluation: {avg_tokens:.2f}")
    
    print("\n🚀 All vacancies successfully processed!")

if __name__ == "__main__":
    main()