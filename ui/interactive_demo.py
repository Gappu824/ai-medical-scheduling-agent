"""
Interactive Demo Component for Preference Matching
RagaAI Assignment - Showcase Interactive Patient Experience
"""

import streamlit as st
import json
from datetime import datetime, timedelta
from typing import Dict, List

def render_interactive_preference_demo():
    """Render an interactive demo showing the preference matching capabilities"""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #e8f5e8, #f0f8f0); padding: 2rem; border-radius: 15px; margin: 1rem 0;">
        <h2 style="color: #2E8B57; text-align: center; margin-bottom: 1rem;">
            🎯 Interactive Preference Matching Demo
        </h2>
        <p style="text-align: center; font-size: 1.1em; color: #333;">
            See how our AI agent actively engages patients to find their perfect appointment match!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Demo scenarios
    demo_tabs = st.tabs([
        "🆕 New Patient Experience", 
        "🔄 Returning Patient Experience", 
        "⭐ Preference Matching Magic"
    ])
    
    with demo_tabs[0]:
        render_new_patient_demo()
    
    with demo_tabs[1]:
        render_returning_patient_demo()
    
    with demo_tabs[2]:
        render_preference_matching_demo()

def render_new_patient_demo():
    """Demo for new patient interactive preference collection"""
    
    st.markdown("### 🆕 New Patient: Discovering Their Perfect Fit")
    
    st.markdown("""
    **The Challenge**: New patients don't know our doctors or locations. Instead of just assigning defaults, 
    our AI **actively helps them discover** what works best for their needs.
    """)
    
    # Interactive demo conversation
    conversation = [
        {
            "role": "assistant",
            "content": """Welcome to MediCare Allergy & Wellness Center! I'm here to help you find the perfect appointment that fits your needs.

I see you're a new patient - that's wonderful! We have multiple doctors and locations, so I'll help you choose what works best for you.

**Our Specialists & What They Treat:**

🔬 **Dr. Sarah Johnson - Allergist**
- Specializes in: Food allergies, environmental allergies, asthma, eczema
- Locations: Main Clinic, Downtown Branch
- Best for: Allergy testing, immunotherapy, chronic allergy management

🫁 **Dr. Michael Chen - Pulmonologist** 
- Specializes in: Asthma, COPD, lung function testing, breathing disorders
- Locations: Main Clinic, Suburban Office
- Best for: Respiratory issues, chronic cough, shortness of breath

🧬 **Dr. Emily Rodriguez - Immunologist**
- Specializes in: Immune system disorders, autoimmune conditions, complex allergies
- Locations: All three locations (most flexible)
- Best for: Complex immune issues, medication allergies, rare conditions

**Which doctor/specialty sounds right for what you're experiencing?** And which location would be most convenient for you?"""
        },
        {
            "role": "user_example",
            "content": "I've been having really bad seasonal allergies and my regular doctor thinks I might need allergy testing. The downtown location would be easiest for me to get to from work."
        },
        {
            "role": "assistant",
            "content": """Perfect! **Dr. Sarah Johnson** is exactly who you need - she's our allergist who specializes in seasonal allergies and allergy testing. And the **Downtown Branch** is a great choice with easy access from downtown.

**Available appointments with Dr. Johnson at Downtown Branch:**

**Tuesday, September 10th**
🌟 9:00 AM ✅ Available (Morning - great for allergy testing!)
🌟 10:30 AM ✅ Available 
• 2:30 PM ✅ Available

**Wednesday, September 11th**
🌟 9:30 AM ✅ Available (Perfect for comprehensive testing)
• 11:00 AM ✅ Available
• 3:00 PM ✅ Available

**Thursday, September 12th**
• 1:00 PM ✅ Available
• 2:30 PM ✅ Available

*I've highlighted morning appointments with 🌟 because they're ideal for allergy testing - you'll get the most accurate results!*

**Which day and time works best for your schedule?**

**Your appointment will be:**
👩‍⚕️ **Doctor:** Dr. Sarah Johnson (Allergist)
🏢 **Location:** Downtown Branch - Medical Center
⏱️ **Duration:** 60 minutes (new patient comprehensive evaluation)"""
        },
        {
            "role": "user_example", 
            "content": "Tuesday morning at 9 AM sounds perfect!"
        },
        {
            "role": "assistant",
            "content": """🎉 **Excellent choice!** Tuesday, September 10th at 9:00 AM is booked for you.

**Your Appointment Confirmation:**
📅 **Date & Time:** Tuesday, September 10th at 9:00 AM
👩‍⚕️ **Doctor:** Dr. Sarah Johnson (Allergist) 
🏢 **Location:** Downtown Branch - Medical Center (789 Medical Center Drive)
⏱️ **Duration:** 60 minutes
🎯 **Focus:** Seasonal allergy evaluation and testing

**What happens next:**
✅ I'll collect your insurance information  
✅ You'll receive confirmation email with directions
✅ Patient intake forms will be emailed (complete 24 hours before visit)
✅ **Important:** Stop all antihistamines 7 days before for accurate testing

**What to bring:**
• Insurance card and photo ID
• List of current medications
• Previous allergy test results (if any)

Ready for the next step? I'll need your insurance information!"""
        }
    ]
    
    render_demo_conversation(conversation)
    
    st.success("""
    **🎯 Key Features Demonstrated:**
    - **Educational Approach**: Explains each doctor's specialty and what they treat
    - **Location Convenience**: Asks about their preferred location based on their needs  
    - **Optimal Scheduling**: Highlights best times for their specific procedure (allergy testing)
    - **Interactive Selection**: Makes it easy to choose with natural language
    - **Complete Information**: Provides all appointment details and next steps
    """)

def render_returning_patient_demo():
    """Demo for returning patient with preference history"""
    
    st.markdown("### 🔄 Returning Patient: Personalized Based on History")
    
    st.markdown("""
    **The Magic**: For returning patients, our AI **remembers their preferences** and offers personalized options 
    based on their history, while still giving them choice and flexibility.
    """)
    
    # Show patient history context
    st.markdown("#### 📊 Patient History Context")
    
    history_data = {
        "Patient": "Sarah Martinez",
        "Previous Visits": 3,
        "Last Doctor": "Dr. Sarah Johnson",
        "Last Location": "Main Clinic", 
        "Last Visit": "2024-06-15 - Follow-up for seasonal allergies",
        "Preference Pattern": "Always chooses morning appointments, prefers same doctor"
    }
    
    col1, col2 = st.columns(2)
    with col1:
        for key, value in list(history_data.items())[:3]:
            st.metric(label=key, value=value)
    with col2:
        for key, value in list(history_data.items())[3:]:
            st.metric(label=key, value=value)
    
    # Interactive conversation
    conversation = [
        {
            "role": "assistant",
            "content": """Welcome back, Sarah! It's wonderful to see you again. 

I see you've been with us for 3 visits, and you've always seen **Dr. Sarah Johnson** at our **Main Clinic** for your seasonal allergy management.

**Would you like to continue with Dr. Johnson at the Main Clinic?** She knows your case well and has all your treatment history. 

**Or would you prefer to try:**
- A different location that might be more convenient?
- One of our other specialists for a second opinion?

*I can also check if Dr. Johnson is available at our other locations if that would work better for your schedule.*

What would work best for you this time?"""
        },
        {
            "role": "user_example",
            "content": "Dr. Johnson has been great, but actually the Downtown location would be much more convenient now that I changed jobs. Can she see me there?"
        },
        {
            "role": "assistant",
            "content": """Perfect! **Dr. Johnson does see patients at the Downtown Branch** - she'll have all your history and treatment records, so it'll be seamless continuity of care at a more convenient location for you.

Since you're a returning patient, this will be a **30-minute follow-up appointment**.

**Dr. Johnson's availability at Downtown Branch:**

**Monday, September 9th**
🌟 9:15 AM ✅ Available (Your usual morning preference!)
🌟 11:30 AM ✅ Available
• 2:00 PM ✅ Available

**Wednesday, September 11th** 
🌟 8:45 AM ✅ Available (Early morning - great for your work schedule)
🌟 10:00 AM ✅ Available
• 1:30 PM ✅ Available

**Friday, September 13th**
🌟 9:30 AM ✅ Available
• 3:45 PM ✅ Available

*I've starred your preferred morning times! Which day works best with your new work schedule?*

**Your appointment details:**
👩‍⚕️ **Doctor:** Dr. Sarah Johnson (your regular allergist)
🏢 **Location:** Downtown Branch - Medical Center  
⏱️ **Duration:** 30 minutes (returning patient follow-up)
📋 **Focus:** Seasonal allergy management follow-up"""
        },
        {
            "role": "user_example",
            "content": "Wednesday morning at 8:45 AM would be perfect - I can stop by before work!"
        },
        {
            "role": "assistant",
            "content": """🎉 **Perfect timing!** Wednesday, September 11th at 8:45 AM is all set.

**Your Appointment Confirmation:**
📅 **Date & Time:** Wednesday, September 11th at 8:45 AM
👩‍⚕️ **Doctor:** Dr. Sarah Johnson (your trusted allergist)
🏢 **Location:** Downtown Branch - Medical Center (789 Medical Center Drive)
⏱️ **Duration:** 30 minutes
🔄 **Visit Type:** Follow-up (returning patient)

**What makes this appointment special:**
✅ **Same trusted doctor** - Dr. Johnson has all your history
✅ **New convenient location** - easy stop before work  
✅ **Optimal timing** - 8:45 AM fits perfectly in your schedule
✅ **Continuity of care** - seamless transition, no need to repeat your history

**What to expect:**
- Quick check-in (you're already in our system!)
- Review of how your current treatment is working
- Any adjustments needed for the upcoming allergy season
- Insurance on file from last visit (we'll verify current coverage)

**Since you're established with Dr. Johnson, you likely won't need new intake forms, but I'll send a brief update form just in case anything has changed.**

Ready to proceed? I just need to verify your current insurance information!"""
        }
    ]
    
    render_demo_conversation(conversation)
    
    st.success("""
    **🎯 Returning Patient Features Demonstrated:**
    - **Personal Recognition**: Acknowledges patient history and previous preferences
    - **Flexible Continuity**: Offers same doctor at different location based on life changes
    - **Preference Memory**: Remembers they prefer morning appointments
    - **Streamlined Process**: 30-minute follow-up vs 60-minute new patient
    - **Contextual Recommendations**: Suggests times that fit their work schedule
    - **Seamless Transition**: Explains how their care history transfers
    """)

def render_preference_matching_demo():
    """Demo showing the preference matching algorithm in action"""
    
    st.markdown("### ⭐ Preference Matching Intelligence")
    
    st.markdown("""
    **The Science**: Our AI doesn't just book appointments - it **learns, adapts, and optimizes** 
    to find the best possible match for each patient's unique needs and constraints.
    """)
    
    # Preference matching visualization
    st.markdown("#### 🧠 How Preference Matching Works")
    
    matching_steps = [
        {
            "step": "1. Context Analysis",
            "description": "Analyze patient type, history, and stated preferences",
            "example": "New patient + 'seasonal allergies' → Allergist recommended"
        },
        {
            "step": "2. Intelligent Questioning", 
            "description": "Ask targeted questions to understand their specific needs",
            "example": "'Which location is most convenient from your work?' → Location preference"
        },
        {
            "step": "3. Educational Guidance",
            "description": "Explain options so patients can make informed choices", 
            "example": "Explain why morning slots are better for allergy testing"
        },
        {
            "step": "4. Smart Availability",
            "description": "Highlight slots that match their preferences and medical needs",
            "example": "🌟 highlight morning appointments for allergy testing"
        },
        {
            "step": "5. Flexible Alternatives",
            "description": "Offer solutions when first choice isn't available",
            "example": "Same doctor at different location, or similar specialist"
        }
    ]
    
    for i, step in enumerate(matching_steps):
        with st.container():
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #2E8B57, #3CB371);
                    color: white;
                    padding: 1rem;
                    border-radius: 10px;
                    text-align: center;
                    font-weight: bold;
                    margin-bottom: 1rem;
                ">
                    {step['step']}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                **{step['description']}**
                
                *Example:* {step['example']}
                """)
        
        if i < len(matching_steps) - 1:
            st.markdown("<div style='text-align: center; margin: 0.5rem 0;'>⬇️</div>", unsafe_allow_html=True)
    
    # Interactive preference scenario
    st.markdown("#### 🎮 Interactive Scenario: Complex Preference Matching")
    
    scenario_type = st.selectbox(
        "Choose a challenging scenario:",
        [
            "Working parent with limited time slots",
            "Patient with mobility issues needing ground floor",
            "Previous bad experience wants different doctor", 
            "Insurance only covers specific locations",
            "Needs urgent appointment but has preferences"
        ]
    )
    
    scenarios = {
        "Working parent with limited time slots": {
            "challenge": "Single parent, can only do early morning (before 8 AM) or late afternoon (after 4 PM)",
            "ai_response": """I understand you need very specific timing as a working parent. Let me check our early and late availability:

**Early Morning Options (Before 8 AM):**
- Dr. Rodriguez has 7:30 AM slots at Suburban Office (quiet, family-friendly)
- Dr. Johnson offers 7:45 AM at Main Clinic (comprehensive allergy center)

**Late Afternoon Options (After 4 PM):**
- Dr. Chen has 4:30 PM at Suburban Office
- Dr. Rodriguez has 5:00 PM at Downtown Branch

**Family-Friendly Features:**
- Suburban Office has a children's play area if you need to bring kids
- We offer same-day sick child coverage if your childcare falls through

Which timing and location combination works best for your family situation?""",
            "solution": "Offers both time ranges, suggests family-friendly location, includes contingency planning"
        },
        
        "Patient with mobility issues needing ground floor": {
            "challenge": "Patient uses wheelchair and needs ground-floor access with nearby parking",
            "ai_response": """I want to make sure you have the most comfortable and accessible experience possible.

**Accessibility-Optimized Options:**

🦽 **Main Clinic - Healthcare Boulevard** (BEST OPTION)
- Ground floor suite with automatic doors
- Designated accessible parking right by entrance  
- Wheelchair-accessible exam rooms
- All our doctors available here

🦽 **Downtown Branch** (Good Alternative)
- Elevator access, accessible parking available
- 2-3 minute walk from parking to suite

*Suburban Office has stairs, so I'd recommend avoiding that location.*

**Available Appointments at Main Clinic:**
- Dr. Johnson: Tuesday 10 AM, Wednesday 2 PM
- Dr. Chen: Monday 11 AM, Thursday 3 PM  
- Dr. Rodriguez: Daily availability

Would you like me to book you at Main Clinic with your preferred doctor? I can also make sure the front desk knows to have someone assist you if needed.""",
            "solution": "Prioritizes accessibility, explains facility features, offers assistance coordination"
        }
    }
    
    if scenario_type in scenarios:
        scenario = scenarios[scenario_type]
        
        st.markdown(f"**Challenge:** {scenario['challenge']}")
        
        with st.expander("See how our AI handles this complex scenario"):
            st.markdown("**AI Response:**")
            st.info(scenario['ai_response'])
            
            st.success(f"**Solution Approach:** {scenario['solution']}")
    
    # Preference learning demonstration
    st.markdown("#### 📈 Preference Learning Over Time")
    
    learning_data = {
        "Visit 1": {
            "preferences": "No stated preferences",
            "choice": "Random assignment → Dr. Johnson, 2 PM",
            "outcome": "Patient mentions they prefer mornings"
        },
        "Visit 2": {
            "preferences": "Learned: Prefers mornings",
            "choice": "Offered morning slots first → 9 AM selected", 
            "outcome": "Patient happy with timing, mentions downtown is convenient"
        },
        "Visit 3": {
            "preferences": "Learned: Morning + Downtown preference",
            "choice": "Dr. Johnson, 9 AM, Downtown offered first",
            "outcome": "Perfect match - patient books immediately"
        }
    }
    
    cols = st.columns(3)
    for i, (visit, data) in enumerate(learning_data.items()):
        with cols[i]:
            st.markdown(f"""
            <div style="
                background: {'#e8f5e8' if i == 2 else '#f8f9fa'};
                border: {'2px solid #2E8B57' if i == 2 else '1px solid #dee2e6'};
                border-radius: 10px;
                padding: 1rem;
                margin-bottom: 1rem;
            ">
                <h4 style="color: #2E8B57; margin-bottom: 0.5rem;">{visit}</h4>
                <p><strong>Preferences:</strong> {data['preferences']}</p>
                <p><strong>AI Choice:</strong> {data['choice']}</p>
                <p><strong>Learning:</strong> {data['outcome']}</p>
            </div>
            """, unsafe_allow_html=True)

def render_demo_conversation(conversation: List[Dict]):
    """Render a demo conversation with proper styling"""
    
    for message in conversation:
        if message["role"] == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(message["content"])
        elif message["role"] == "user_example":
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"*Example patient response:*\n\n{message['content']}")
        else:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

# Example usage in main Streamlit app
if __name__ == "__main__":
    st.set_page_config(page_title="Interactive Preference Demo", layout="wide")
    render_interactive_preference_demo()