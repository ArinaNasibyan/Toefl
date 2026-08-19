import re
from pathlib import Path

# Advanced American English IPA mapping overrides for all problematic words
OVERRIDES = {
    # Pronunciation corrections
    "hypothesis": "/haɪˈpɑːθəsɪs/",
    "synthesis": "/ˈsɪnθəsɪs/",
    "analysis": "/əˈnæləsɪs/",
    "catalyst": "/ˈkætəlɪst/",
    "ecosystem": "/ˈikoʊˌsɪstəm/",
    "biodiversity": "/ˌbaɪoʊdaɪˈvərsəti/",
    "greenhouse": "/ˈɡrinˌhaʊs/",
    "infrastructure": "/ˈɪnfrəˌstrʌktʃər/",
    "cybernetics": "/ˌsaɪbərˈnɛtɪks/",
    "biotechnology": "/ˌbaɪoʊtɛkˈnɑːlədʒi/",
    "algorithm": "/ˈælɡərɪðəm/",
    "mechanism": "/ˈmɛkənɪzəm/",
    "frequency": "/ˈfrikwənsi/",
    "excavate": "/ˈɛkskəveɪt/",
    "precursor": "/priˈkɜːrsər/",
    "cognition": "/kɑːɡˈnɪʃən/",
    "conditioning": "/kənˈdɪʃənɪŋ/",
    "bureaucracy": "/bjuˈrɑːkrəsi/",
    "egalitarian": "/ɪˌɡælɪˈtɛriən/",
    "velocity": "/vəˈlɑːsəti/",
    "acidification": "/əˌsɪdɪfɪˈkeɪʃən/",
    "biodegradable": "/ˌbaɪoʊdɪˈɡreɪdəbəl/",
    "carbon": "/ˈkɑːrbən/",
    "monarchy": "/ˈmɑːnərki/",
    "oligarchy": "/ˈɑːlɪˌɡɑːrki/",
    "democracy": "/dɪˈmɑːkrəsi/",
    "treatise": "/ˈtritɪs/",
    "hierarchy": "/ˈhaɪərɑːrki/",
    "epoch": "/ˈɛpək/",
    "stimulus": "/ˈstɪmjʊləs/",
    "physiological": "/ˌfɪziəˈlɑːdʒɪkəl/",
    "anatomical": "/ˌænəˈtɑːmɪkəl/",
    "metabolism": "/məˈtæbəlɪzəm/",
    "specimen": "/ˈspɛsəmən/",
    "pathogen": "/ˈpæθədʒən/",
    "evolutionary": "/ˌɛvəˈluːʃənɛri/",
    "photosynthesis": "/ˌfoʊtoʊˈsɪnθəsɪs/",
    "organism": "/ˈɔːrɡənˌɪzəm/",
    "sustainable": "/səˈsteɪnəbəl/",
    "agriculture": "/ˈæɡrɪˌkʌltʃər/",
    "artificial": "/ˌɑːrtɪˈfɪʃəl/",
    "intelligence": "/ɪnˈtɛlɪdʒəns/",
    "domesticate": "/dəˈmɛstɪkeɪt/",
    "precipitation": "/prɪˌsɪpɪˈteɪʃən/",
    "evaporation": "/ɪˌvæpəˈreɪʃən/",
    "condensation": "/ˌkɑːndɛnˈseɪʃən/",
    "semi-arid": "/ˌsɛmiˈærɪd/",
    "emissions": "/iˈmɪʃənz/",
    "acquire": "/əˈkwaɪər/",
    "cellular": "/ˈsɛljələr/",
    "apparent": "/əˈpærənt/",
    "approach": "/əˈproʊtʃ/",
    "equilibrium": "/ˌikwɪˈlɪbriəm/",
    "conduction": "/kənˈdʌkʃən/",
    "convection": "/kənˈvɛkʃən/",
    "radiation": "/ˌreɪdiˈeɪʃən/",
    "diffusion": "/dɪˈfjuːʒən/",
    "respiration": "/ˌrɛspəˈreɪʃən/",
    "abundant": "/əˈbʌndənt/",
    "adequate": "/ˈædəkwət/",
    "advocate": "/ˈædvəkeɪt/",
    "allocate": "/ˈæləkeɪt/",
    "ambiguous": "/æmˈbɪɡjuəs/",
    "analyze": "/ˈænəlaɪz/",
    "assess": "/əˈsɛs/",
    "beneficial": "/ˌbɛnəˈfɪʃəl/",
    "coherent": "/koʊˈhɪrənt/",
    "derive": "/dɪˈraɪv/",
    "distinct": "/dɪˈstɪŋkt/",
    "emerge": "/iˈmərdʒ/",
    "emphasize": "/ˈɛmfəsaɪz/",
    "imply": "/ɪmˈplaɪ/",
    "significant": "/sɪɡˈnɪfɪkənt/",
    "empirical": "/ɛmˈpɪrɪkəl/",
    "friction": "/ˈfrɪkʃən/",
    "nucleus": "/ˈnuːkliəs/",
    "toxic": "/ˈtɑːksɪk/",
    "sustain": "/səˈsteɪn/",
    "fertilizer": "/ˈfɜːrtəlaɪzər/",
    "degrade": "/dɪˈɡreɪd/",
    "canopy": "/ˈkænəpi/",
    "organic": "/ɔːrˈɡænɪk/",
    "extinct": "/ɛkˈstɪŋkt/",
    "fauna": "/ˈfɔːnə/",
    "transmission": "/trænzˈmɪʃən/",
    "protocol": "/ˈproʊtəˌkɑːl/",
    "wavelength": "/ˈweɪvˌlɛŋkθ/",
    "legacy": "/ˈlɛɡəsi/",
    "preservation": "/ˌprɛzərˈveɪʃən/",
    "perception": "/pərˈsɛpʃən/",
    "sovereignty": "/ˈsɑːvrənti/",
    "conflict": "/ˈkɑːnflɪkt/",
    "alliance": "/əˈlaɪəns/",
    "treaty": "/ˈtriti/",
    "revolution": "/ˌrɛvəˈluːʃən/",
    "stratigraphy": "/strəˈtɪɡrəfi/",
    "innovation": "/ˌɪnəˈveɪʃən/",
    "robotics": "/roʊˈbɑːtɪks/",
    "shrine": "/ʃraɪn/",
    "simulation": "/ˌsɪmjʊˈleɪʃən/",
    "compile": "/kənˈpaɪl/",
    "valid": "/ˈvælɪd/",
    "abstract": "/ˈæbstrækt/",
    "accurate": "/ˈækjərət/",
    "brief": "/brif/",
    "capable": "/ˈkeɪpəbəl/",
    "displace": "/dɪsˈpleɪs/",
    "diversity": "/daɪˈvərsəti/",
    "exceed": "/ɪkˈsid/",
    "exhibit": "/ɪɡˈzɪbɪt/",
    "federal": "/ˈfɛdərəl/",
    "furthermore": "/ˌfərdərˈmɔːr/",
    "ignorant": "/ˈɪɡnərənt/",
    "incentive": "/ɪnˈsɛntɪv/",
    "lecture": "/ˈlɛktʃər/",
    "maximum": "/ˈmæksəməm/",
    "minimize": "/ˈmɪnəˌmaɪz/",
    "nevertheless": "/ˌnɛvərðəˈlɛs/",
    "precise": "/prɪˈsaɪs/",
    "radical": "/ˈrædɪkəl/",
    "reveal": "/rɪˈvil/",
    "scope": "/skoʊp/",
    "underlying": "/ˌʌndərˈlaɪɪŋ/",
    "widespread": "/ˈwaɪdˌsprɛd/",
    "complement": "/ˈkɑːmpləmənt/",
    "cooperate": "/koʊˈɑːpəˌreɪt/",
    "framework": "/ˈfreɪmˌwərk/",
    "hypothesize": "/haɪˈpɑːθəˌsaɪz/",
    "justify": "/ˈdʒʌstəˌfaɪ/",
    "primary": "/ˈpraɪˌmɛri/",
    "terminate": "/ˈtərməˌneɪt/",
    "ultimate": "/ˈʌltəmət/",
    "undergo": "/ˌʌndərˈɡoʊ/",
    "virtually": "/ˈvərtʃuəli/",
    "uniform": "/ˈjunəˌfɔːrm/",
    "temporary": "/ˈtɛmpəˌrɛri/",
    "subordinate": "/səˈbɔːrdənət/",
    "sphere": "/sfɪr/",
    "scenario": "/səˈnɛrioʊ/",
    "bias": "/ˈbaɪəs/",
    "cohere": "/koʊˈhɪr/",
    "compound": "/ˈkɑːmpaʊnd/",
    "confine": "/kənˈfaɪn/",
    "consent": "/kənˈsɛnt/",
    "constitute": "/ˈkɑːnstəˌtuːt/",
    "constrain": "/kənˈstreɪn/",
    "contradict": "/ˌkɑːntrəˈdɪkt/",
    "controversy": "/ˈkɑːntrəˌvərsi/",
    "equivalent": "/ɪˈkwɪvələnt/",
    "fluctuate": "/ˈflʌktʃuˌeɪt/",
    "implicit": "/ɪmˈplɪsɪt/",
    "induce": "/ɪnˈduːs/",
    "inevitable": "/ɪnˈɛvɪtəbəl/",
    "inherent": "/ɪnˈhɪrənt/",
    "intensity": "/ɪnˈtɛnsəti/",
    "logic": "/ˈlɑːdʒɪk/",
    "margin": "/ˈmɑːrdʒɪn/",
    "neutral": "/ˈnuːtrəl/",
    "nuclear": "/ˈnuːkliər/",
    "passive": "/ˈpæsɪv/",
    "practitioner": "/prækˈtɪʃənər/",
    "qualitative": "/ˈkwɑːlɪˌteɪtɪv/",
    "ratio": "/ˈreɪʃioʊ/",
    "refine": "/rɪˈfaɪn/",
    "rigid": "/ˈrɪdʒɪd/",
    "agrarian": "/əˈgrɛriən/",
    
    # Newly identified weird database records:
    "reproduce": "/ˌriprəˈdus/",
    "resilience": "/rɪˈzɪliəns/",
    "thermodynamics": "/ˌθərmoʊdaɪˈnæmɪks/",
    "conservation": "/ˌkɑːnsərˈveɪʃən/",
    "deforestation": "/ˌdifɔːrəˈsteɪʃən/",
    "meteorological": "/ˌmiːtiərəˈlɑːdʒɪkəl/",
    "reclamation": "/ˌrɛkləˈmeɪʃən/",
    "afforestation": "/əˌfɔːrəˈsteɪʃən/",
    "biosphere": "/ˈbaɪoʊˌsfɪr/",
    "ecology": "/ɪˈkɑːlədʒi/",
    "conserve": "/kənˈsərv/",
    "pollutant": "/pəˈlutənt/",
    "osmosis": "/ɑːzˈmoʊsɪs/",
    "geological": "/ˌdʒiəˈlɑːdʒɪkəl/",
    "excavation": "/ˌɛkskəˈveɪʃən/",
    "renaissance": "/ˈrɛnəˌsɑːns/",
    "colonization": "/ˌkɑːlənəˈzeɪʃən/",
    "imperialism": "/ɪmˈpɪriəlˌɪzəm/",
    "capitalism": "/ˈkæpətəlˌɪzəm/",
    "liability": "/ˌlaɪəˈbɪlɪti/",
    "marginalization": "/ˌmɑːrdʒɪnələˈzeɪʃən/",
    "evaluate": "/ɪˈvæljʊeɪt/",
    "monetary": "/ˈmɑːnəˌtɛri/",
    "virtual": "/ˈvərtʃuəl/",
    "cybersecurity": "/ˌsaɪbərsɪˈkjʊrəti/",
    "demographics": "/ˌdɛməˈɡræfɪks/",
    "software": "/ˈsɔːftˌwɛr/",
    "satellite": "/ˈsætəlaɪt/",
    "secretion": "/sɪˈkriːʃən/",
}

def clean_ipa(word, ipa):
    if not ipa:
        return ipa
        
    w_clean = word.strip().lower()
    if w_clean in OVERRIDES:
        return OVERRIDES[w_clean]
        
    # Standard rules-based conversions for everything else
    # Consonants
    ipa = ipa.replace("ɹ", "r")
    ipa = ipa.replace("͡", "")
    ipa = ipa.replace(".", "")
    ipa = ipa.replace(" ", "")
    
    # Remove tie / slur accent markers
    ipa = ipa.replace("̯", "")
    
    # Syllabics
    ipa = ipa.replace("n̩", "ən")
    ipa = ipa.replace("l̩", "əl")
    ipa = ipa.replace("m̩", "əm")
    
    # Process parentheses
    # (ə) -> ə
    ipa = ipa.replace("(ə)", "ə")
    # (t) -> t
    ipa = ipa.replace("(t)", "t")
    # Remove any other parentheses and content inside them like (r), (j)
    ipa = re.sub(r'\([a-zA-Z]\)', '', ipa)
    
    # Vowels
    ipa = ipa.replace("ɒ", "ɑ")
    ipa = ipa.replace("əʊ", "oʊ")
    ipa = ipa.replace("ɜː", "ər")
    ipa = ipa.replace("ɜ", "ər")
    ipa = ipa.replace("ɜr", "ər")
    
    # Rhoticity check for aː
    if "ɑː" in ipa:
        if "r" in w_clean:
            ipa = ipa.replace("ɑː", "ɑr")
        else:
            ipa = ipa.replace("ɑː", "ɑ")
            
    # Rhoticity check for ɔː
    if "ɔː" in ipa or "ɔ:" in ipa:
        target = "ɔː" if "ɔː" in ipa else "ɔ:"
        if "r" in w_clean:
            ipa = ipa.replace(target, "ɔr")
        else:
            ipa = ipa.replace(target, "ɔ")
            
    # Simplify near, square, cure
    ipa = ipa.replace("ɛə", "ɛr")
    ipa = ipa.replace("ɪə", "ɪr")
    ipa = ipa.replace("ʊə", "ʊr")
    
    # Simplify high central vowels
    ipa = ipa.replace("ɨ", "ɪ")
    ipa = ipa.replace("ʉ", "ʊ")
    ipa = ipa.replace("ɵ", "oʊ")
    ipa = ipa.replace("ɝ", "ər")
    ipa = ipa.replace("ɚ", "ər")
    
    # Simplify long vowels
    ipa = ipa.replace("iː", "i")
    ipa = ipa.replace("uː", "u")
    
    # Fix non-rhotic endings if spelling suggests rhotic
    if w_clean.endswith(("er", "or", "ar", "re", "r")):
        if ipa.endswith("ə/"):
            ipa = ipa[:-2] + "ər/"
        elif ipa.endswith("ə"):
            ipa = ipa[:-1] + "ər"
            
    # Double letter cleanups
    ipa = ipa.replace("rr", "r")
    ipa = ipa.replace("ərər", "ər")
    
    return ipa

def process_file():
    target_path = Path("scripts/generate_vocab.py")
    if not target_path.exists():
        print("Error: scripts/generate_vocab.py not found.")
        return
        
    print(f"Reading {target_path}...")
    content = target_path.read_text(encoding="utf-8")
    
    # Replace EXISTING_WORDS transcriptions
    def replace_existing_transcription(match):
        block = match.group(0)
        word_match = re.search(r'"word":\s*"([^"]+)"', block)
        trans_match = re.search(r'"transcription":\s*"([^"]+)"', block)
        if word_match and trans_match:
            word = word_match.group(1)
            old_trans = trans_match.group(1)
            new_trans = clean_ipa(word, old_trans)
            block = block.replace(trans_match.group(0), f'"transcription": "{new_trans}"')
            
            log_line = f"EXISTING: {word} -> {new_trans}"
            print(log_line.encode('ascii', errors='ignore').decode('ascii'))
        return block

    content = re.sub(r'\{\s*"id":\s*"vocab_\d+",\s*"word":\s*"[^"]+",\s*"translation":\s*"[^"]+",\s*"transcription":\s*"[^"]+",[^}]*\}', replace_existing_transcription, content)
    
    # Process NEW_WORDS_RAW list of tuples
    def replace_new_word_tuple(match):
        word = match.group(1)
        translation = match.group(2)
        transcription = match.group(3)
        example = match.group(4)
        level = match.group(5)
        
        new_trans = clean_ipa(word, transcription)
        
        log_line = f"NEW: {word} -> {new_trans}"
        print(log_line.encode('ascii', errors='ignore').decode('ascii'))
        return f'("{word}", "{translation}", "{new_trans}", "{example}", "{level}")'
        
    pattern = r'\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)'
    content = re.sub(pattern, replace_new_word_tuple, content)
    
    print(f"Writing updated content to {target_path}...")
    target_path.write_text(content, encoding="utf-8")
    print("Done updating generate_vocab.py!")

if __name__ == "__main__":
    process_file()
