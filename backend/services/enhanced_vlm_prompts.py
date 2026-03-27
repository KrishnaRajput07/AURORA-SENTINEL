def build_vlm_prompt_enhanced(ml_objects: list, ml_weapons: list, prev_description: str = "", timestamp: float = 0.0) -> str:
    """
    Build an enhanced, context-rich prompt for detailed forensic VLM analysis.
    Focus on generating comprehensive, actionable descriptions.
    """
    # Enhanced ML context with more detail
    ml_context = ""
    if ml_weapons:
        weapon_details = []
        for w in ml_weapons:
            class_name = w.get('sub_class', w.get('class', 'weapon'))
            confidence = w.get('confidence', 0)
            bbox = w.get('bbox', [])
            if bbox:
                position = f"center-right" if bbox[0] > 0.5 else "center-left"
                weapon_details.append(f"{class_name} ({confidence:.0%} confidence, {position})")
            else:
                weapon_details.append(f"{class_name} ({confidence:.0%} confidence)")
        ml_context += f"⚠️ WEAPONS DETECTED: {', '.join(weapon_details)}. "
    
    if ml_objects:
        persons = [o for o in ml_objects if o.get('class') == 'person']
        vehicles = [o for o in ml_objects if o.get('class') in ['car', 'truck', 'motorcycle']]
        other_objects = [o for o in ml_objects if o.get('class') not in ['person', 'car', 'truck', 'motorcycle']]
        
        if persons:
            person_details = []
            for p in persons[:5]:  # Limit to first 5 people
                conf = p.get('confidence', 0)
                bbox = p.get('bbox', [])
                if bbox:
                    x_center = (bbox[0] + bbox[2]) / 2
                    position = "right side" if x_center > 0.5 else "left side"
                    person_details.append(f"Person ({conf:.0%}, {position})")
                else:
                    person_details.append(f"Person ({conf:.0%})")
            ml_context += f"👥 {len(persons)} person(s) detected: {', '.join(person_details)}. "
        
        if vehicles:
            vehicle_names = [v.get('class', 'vehicle') for v in vehicles]
            ml_context += f"🚗 Vehicles detected: {', '.join(set(vehicle_names))}. "
        
        if other_objects:
            other_names = [o.get('class', 'object') for o in other_objects]
            ml_context += f"📦 Objects: {', '.join(set(other_names))}. "

    # Temporal context
    time_context = f"Timestamp: {timestamp:.2f}s"
    
    # Previous frame context
    context_note = ""
    if prev_description:
        context_note = f"\n📝 Previous analysis: {prev_description[:150]}..."

    return (
        f"🔍 DETAILED SURVEILLANCE FORENSIC ANALYSIS {time_context}{context_note}\n"
        f"🤖 ML PRE-SCAN: {ml_context or 'No specific ML flags'}\n\n"
        "TASK: Provide a comprehensive forensic analysis of this surveillance frame. "
        "Focus on actionable intelligence that would help security personnel.\n\n"
        
        "📋 REQUIRED ANALYSIS SECTIONS:\n"
        "1. 🎯 SCENE OVERVIEW: "
        "- Location type (indoor/outdoor, street, building, venue)\n"
        "- Lighting conditions and visibility\n"
        "- Number of people and their general positions\n"
        "- Notable objects or environmental factors\n\n"
        
        "2. 👥 PERSON ANALYSIS: "
        "- For each person: approximate age, gender, clothing, distinctive features\n"
        "- Body language and posture (aggressive, defensive, neutral, fleeing)\n"
        "- Facial expressions if visible (angry, fearful, calm, determined)\n"
        "- Hand positions (visible, hidden, holding objects)\n"
        "- Group dynamics (alone, pair, group, leader/follower)\n\n"
        
        "3. ⚡ INTERACTION ANALYSIS: "
        "- Describe all interactions between people in detail\n"
        "- Nature of contact (physical, verbal, threatening, peaceful)\n"
        "- Power dynamics and escalation indicators\n"
        "- Any weapons or dangerous objects involved\n"
        "- Distance and proximity between individuals\n\n"
        
        "4. 🚨 THREAT ASSESSMENT: "
        "- Identify specific threats (weapons, violence, aggression)\n"
        "- Distinguish between sport, prank, and real threats\n"
        "- Assess immediacy and severity of any danger\n"
        "- Note any suspicious behavior or indicators\n\n"
        
        "5. 📊 RISK CLASSIFICATION: "
        "Provide RISK SCORE: [0-100] where:\n"
        "0-20: Safe/Normal activity\n"
        "21-40: Minor concern (suspicious but not threatening)\n"
        "41-60: Suspicious activity (monitor closely)\n"
        "61-80: High threat (immediate attention needed)\n"
        "81-100: Critical danger (emergency response required)\n\n"
        
        "6. 🔎 FORENSIC DETAILS: "
        "- Any identifiable features (tattoos, scars, distinctive clothing)\n"
        "- Direction of movement or escape routes\n"
        "- Potential witnesses or bystanders\n"
        "- Environmental factors affecting visibility or escape\n"
        "- Anything that would help in identification or investigation\n\n"
        
        "📝 OUTPUT FORMAT: "
        "Write as a professional security report. Be specific and detailed. "
        "End with your risk assessment on the final line: RISK SCORE: [number]"
    )


def build_contextual_prompts(risk_level: int, scene_type: str = "") -> str:
    """
    Generate context-specific prompts for different risk levels and scenarios.
    """
    prompts = {
        "critical_weapon": (
            "🚨 CRITICAL WEAPON ANALYSIS REQUIRED\n"
            "Focus on: Weapon type, handling proficiency, target, intent, "
            "immediacy of threat, and potential for harm. "
            "Describe the weapon holder's demeanor and any victims."
        ),
        "physical_violence": (
            "⚔️ PHYSICAL VIOLENCE ANALYSIS\n"
            "Detail: Type of violence, participants, injuries, escalation, "
            "weapons involved, crowd reaction, and intervention needs."
        ),
        "suspicious_behavior": (
            "🔍 SUSPICIOUS BEHAVIOR ANALYSIS\n"
            "Analyze: Unusual actions, concealed objects, surveillance behavior, "
            "reconnaissance activities, and potential pre-attack indicators."
        ),
        "crowd_disturbance": (
            "👥 CROWD DISTURBANCE ANALYSIS\n"
            "Assess: Crowd size,情绪 (emotions), escalation potential, "
            "leaders, flash points, and safety concerns."
        ),
        "fall_detection": (
            "🏥 FALL/INJURY ANALYSIS\n"
            "Determine: Cause of fall (accident vs push vs trip), injury severity, "
            "response of others, and medical needs."
        ),
        "sport_activity": (
            "🏟️ SPORT ACTIVITY VERIFICATION\n"
            "Confirm: Sport type, equipment, uniforms, officials, "
            "controlled environment vs uncontrolled aggression."
        )
    }
    
    if risk_level >= 85:
        return prompts.get("critical_weapon", prompts["physical_violence"])
    elif "fall" in scene_type.lower():
        return prompts["fall_detection"]
    elif "sport" in scene_type.lower():
        return prompts["sport_activity"]
    elif risk_level >= 60:
        return prompts["physical_violence"]
    elif risk_level >= 40:
        return prompts["suspicious_behavior"]
    else:
        return "🔍 GENERAL SECURITY MONITORING: Report any unusual or noteworthy activity."
