#!/usr/bin/env python3
"""
Resume Processing Module

This script processes CVs and vacancies by:
1. Fetching new vacancies from the CSV
2. Comparing CVs with vacancies via embeddings
3. Evaluating matches using GPT-4
4. Updating the vacancy status in the CSV

Author: Daniel Tromp
Version: 1.0.0
Created: 2024-02-14
License: MIT
"""

import csv
import json
import re
from collections import defaultdict
from openai import OpenAI
import tiktoken
import lancedb
from config import OPENAI_API_KEY, EMBEDDING_MODEL, MATCH_THRESHOLD, MATCH_COUNT, EXCLUDED_CLIENTS

# Initialiseer OpenAI client en token encoder
client_openai = OpenAI(api_key=OPENAI_API_KEY)
enc = tiktoken.encoding_for_model("gpt-4o-mini")

CSV_VACANCIES = "vacancies.csv"

def load_vacancies_from_csv() -> list:
    """Load vacancies with status 'New' from CSV file."""
    with open(CSV_VACANCIES, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader if row.get("Status", "").lower() == "nieuw"]

def update_vacancy_in_csv(vacancy_id: str, update_data: dict) -> None:
    """Update a specific vacancy in the CSV file."""
    with open(CSV_VACANCIES, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        vacancies = list(reader)
        fieldnames = reader.fieldnames

    for row in vacancies:
        if row.get("URL", "") == vacancy_id:
            row.update(update_data)

    with open(CSV_VACANCIES, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(vacancies)

def get_embedding(text: str) -> list:
    """Generate an embedding for the given text."""
    response = client_openai.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

def search_candidates(vacancy_embedding: list,
                      collection,
                      match_threshold: float,
                      match_count: int) -> list:
    """Search candidates based on vector similarity."""
    results = collection.search(query=vacancy_embedding)\
        .limit(match_count)\
        .select(["context", "cv_chunk", "_distance"])\
        .to_list()
    return [r for r in results if r["_distance"] <= match_threshold]

def extract_candidate_name(context: str) -> str:
    """
    Extraheert de kandidaatnaam uit de context.
    Verwacht format: "Chunk X van filename.pdf"
    """
    parts = context.split("van")
    if len(parts) > 1:
        filename = parts[1].strip()
        return filename.replace(".pdf", "")
    return "Onbekend"

def evaluate_candidate(name: str, cv_text: str, vacancy_text: str) -> dict:
    """Evaluates a candidate and returns a JSON-structured result."""
    prompt = (
        "Evalueer de geschiktheid van een kandidaat voor een specifieke vacature op basis van de opgegeven functiebeschrijving en CV.\n\n"
        "**Functieomschrijving:**\n"
        f"{vacancy_text}\n\n"
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
        "   - Weeg dit zwaar mee in het percentage\n"
        "2. **Relevantie van werkervaring:** Hoe goed sluit de werkervaring van de kandidaat aan bij de functie? "
        "Is de ervaring **strategisch, operationeel of hands-on**?\n"
        "3. **Vaardigheden match:** Heeft de kandidaat de vereiste vaardigheden en hoe sterk zijn ze aanwezig?\n"
        "4. **Praktische inzetbaarheid:** Is de kandidaat direct inzetbaar of is er een leercurve?\n"
        "5. **Risico's:** Zijn er risico's door gebrek aan specifieke ervaring, werkstijl of een te groot verschil met de functie?\n\n"
        "### **Uitvoer:**\n"
        "- **Percentage (0-100%)** op basis van hoe goed de kandidaat past bij de functie.\n"
        "  Als de vacature een stap terug is in functieniveau, geef dan maximaal 40% match.\n"
        "- **Sterke punten** van de kandidaat.\n"
        "- **Zwakke punten** en aandachtspunten.\n"
        "- **Eindoordeel** of de kandidaat geschikt is, met argumentatie.\n"
        "  Begin het eindoordeel met een duidelijke analyse van het functieniveau verschil.\n\n"
        "Geef je antwoord in JSON formaat met de volgende velden: name, percentage, sterke_punten, zwakke_punten, eindoordeel"
    )

    response = client_openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "Je bent een ervaren HR-specialist. Geef alleen JSON output terug. "
                "Als het percentage <60% is, geef een korte onderbouwing waarom de match laag is. "
                "Als het percentage >=60% is, geef een uitgebreide onderbouwing met prioriteiten "
                "per verbeterpunt, waarbij je percentages toevoegt die exact optellen tot (100% - het percentage)."
            )},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    evaluation = json.loads(response.choices[0].message.content)
    evaluation['name'] = name  # Voeg de kandidaatnaam toe aan de evaluatie
    return evaluation

def process_vacancy(vacancy_text: str, candidate_matches: dict) -> dict:
    """Process one vacancy and evaluate all candidates."""
    evaluations = []

    for name, chunks in candidate_matches.items():
        cv_text = " ".join(chunks)
        evaluation = evaluate_candidate(name, cv_text, vacancy_text)
        evaluations.append(evaluation)

    sorted_evaluations = sorted(evaluations,
                                key=lambda x: x.get("percentage", 0),
                                reverse=True)
    top_evaluations = sorted_evaluations[:5]
    best_match = top_evaluations[0] if top_evaluations else None

    if best_match:
        return {
            "Status": "Open" if best_match.get("percentage", 0) >= 60 else "AI afgewezen",
            "Checked_resumes": ", ".join(eval.get("name", "") for eval in top_evaluations),
            "Top_Match": best_match.get("percentage", 0),
            "Matches": json.dumps({"alle_matches": top_evaluations},
                                  ensure_ascii=False, indent=2)
        }
    return None

def main():
    """Main function for processing vacancies."""
    vacancies = load_vacancies_from_csv()
    print(f"Processing {len(vacancies)} new vacancies...")

    db = lancedb.connect("lancedb")
    collection = db.open_table("resumes")

    for vacancy in vacancies:
        vacancy_id = vacancy.get("URL", "")
        klant = vacancy.get("Klant", "").strip()

        if klant in EXCLUDED_CLIENTS:
            update_vacancy_in_csv(vacancy_id, {"Status": "AI_rejected"})
            continue

        vacancy_text = vacancy.get("Functieomschrijving", "")
        vacancy_embedding = get_embedding(vacancy_text)
        results = search_candidates(vacancy_embedding, collection, MATCH_THRESHOLD, MATCH_COUNT)

        # Groepeer resultaten op basis van de kandidaatnaam uit de context
        candidate_matches = defaultdict(list)
        for item in results:
            candidate_name = extract_candidate_name(item["context"])
            candidate_matches[candidate_name].append(item["cv_chunk"])

        if candidate_matches:
            result = process_vacancy(vacancy_text, candidate_matches)
            if result:
                update_vacancy_in_csv(vacancy_id, result)
        else:
            update_vacancy_in_csv(vacancy_id, {"Status": "AI_rejected"})

    print("Processing complete.")

if __name__ == "__main__":
    main()