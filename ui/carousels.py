"""
UI Carousels Module
Carousel components for displaying interesting facts and architectural decisions.
"""

import random
import streamlit as st


def show_fact_carousel():
    """
    Display a carousel of interesting facts using HTML/JavaScript to avoid Streamlit reruns.
    
    Shows rotating facts about electric buses and CP-SAT solver.
    """
    facts = [
        "CP-SAT can handle millions of variables and constraints efficiently",
        "Electric buses can save up to 70% on fuel costs compared to diesel",
        "Fast charging takes 25 minutes for full charge in this system",
        "This scheduler uses Google's OR-Tools CP-SAT library",
        "Electric buses have zero tailpipe emissions",
        "CP-SAT is used by major companies for logistics optimization",
        "Battery range is 240km for buses in this system",
        "The solver uses constraint programming to find optimal schedules",
        "Electric buses are quieter than traditional diesel buses"
    ]
    
    # Create HTML/JavaScript carousel with beautiful styling
    html_code = f"""
    <div style="padding: 0.25rem; background: linear-gradient(135deg, #172d43 0%, #2a4a6f 100%); border-radius: 0.75rem; margin: 0; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2); height: 100%; box-sizing: border-box; padding-inline: 1rem;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 15px; height: 100%;">
            <button onclick="prevFact()" style="padding: 10px 18px; cursor: pointer; background: rgba(255, 255, 255, 0.2); color: white; border: 2px solid rgba(255, 255, 255, 0.3); border-radius: 8px; font-size: 16px; transition: all 0.3s ease; backdrop-filter: blur(10px);">←</button>
            <div style="flex: 1; text-align: center;">
                <div style="color: white; font-weight: 600; margin-bottom: 6px; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Did you know?</div>
                <div id="fact-display" style="color: rgba(255, 255, 255, 0.95); font-size: 14px; line-height: 1.5; min-height: 35px; display: flex; align-items: center; justify-content: center;">{facts[0]}</div>
                <div id="fact-counter" style="color: rgba(255, 255, 255, 0.7); font-size: 12px; margin-top: 8px; font-weight: 500;">Fact 1 of {len(facts)}</div>
            </div>
            <button onclick="nextFact()" style="padding: 10px 18px; cursor: pointer; background: rgba(255, 255, 255, 0.2); color: white; border: 2px solid rgba(255, 255, 255, 0.3); border-radius: 8px; font-size: 16px; transition: all 0.3s ease; backdrop-filter: blur(10px);">→</button>
        </div>
    </div>
    <style>
        html {{
            background-color: #0e1117;
            font-family: "Source Sans Pro", sans-serif;
        }}
        * {{
            box-sizing: border-box;
        }}
        button:hover {{
            background: rgba(255, 255, 255, 0.3) !important;
            transform: scale(1.05);
        }}
        #fact-display {{
            transition: opacity 0.3s ease;
        }}
    </style>
    <script>
        var facts = {facts};
        var currentIndex = 0;
        var autoRotateInterval = null;
        
        function updateDisplay() {{
            var factDisplay = document.getElementById('fact-display');
            factDisplay.style.opacity = '0';
            setTimeout(function() {{
                factDisplay.textContent = facts[currentIndex];
                factDisplay.style.opacity = '1';
            }}, 150);
            
            document.getElementById('fact-counter').textContent = 'Fact ' + (currentIndex + 1) + ' of ' + facts.length;
        }}
        
        function nextFact() {{
            currentIndex = (currentIndex + 1) % facts.length;
            updateDisplay();
        }}
        
        function prevFact() {{
            currentIndex = (currentIndex - 1 + facts.length) % facts.length;
            updateDisplay();
        }}
        
        // Start automatic rotation every 5 seconds
        function startAutoRotate() {{
            if (autoRotateInterval) {{
                clearInterval(autoRotateInterval);
            }}
            autoRotateInterval = setInterval(nextFact, 5000);
        }}
        
        // Start auto-rotation on load
        startAutoRotate();
    </script>
    """
    
    st.components.v1.html(html_code, height=100)


def show_arch_decisions_carousel():
    """
    Display a carousel of architectural decisions using HTML/JavaScript to avoid Streamlit reruns.
    
    Shows rotating architectural decisions made during development.
    """
    decisions = [
        "CP-SAT constraint programming chosen for scalability with millions of variables",
        "Streamlit caching (@st.cache_data) for scenario loading and scheduler runs",
        "Modular architecture: loader, scheduler, utils for separation of concerns",
        "Time limit optimization ensures guaranteed feasible solutions within 60s",
        "Weight-based objective function balances individual vs operator vs overall optimization",
        "Optimizations refine initial feasible solution for better quality",
        "Scenario-based configuration allows testing different operational contexts",
        "Dynamic bus generation enables on-demand fleet simulation"
    ]
    
    # Create HTML/JavaScript carousel with beautiful styling
    html_code = f"""
    <div style="padding: 0.25rem; background: linear-gradient(135deg, #172d43 0%, #2a4a6f 100%); border-radius: 0.75rem; margin: 0; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2); height: 100%; box-sizing: border-box; padding-inline: 1rem;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 15px; height: 100%;">
            <button onclick="prevDecision()" style="padding: 10px 18px; cursor: pointer; background: rgba(255, 255, 255, 0.2); color: white; border: 2px solid rgba(255, 255, 255, 0.3); border-radius: 8px; font-size: 16px; transition: all 0.3s ease; backdrop-filter: blur(10px);">←</button>
            <div style="flex: 1; text-align: center;">
                <div style="color: white; font-weight: 600; margin-bottom: 6px; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Architecture Decision</div>
                <div id="decision-display" style="color: rgba(255, 255, 255, 0.95); font-size: 14px; line-height: 1.5; min-height: 35px; display: flex; align-items: center; justify-content: center;">{decisions[0]}</div>
                <div id="decision-counter" style="color: rgba(255, 255, 255, 0.7); font-size: 12px; margin-top: 8px; font-weight: 500;">Decision 1 of {len(decisions)}</div>
            </div>
            <button onclick="nextDecision()" style="padding: 10px 18px; cursor: pointer; background: rgba(255, 255, 255, 0.2); color: white; border: 2px solid rgba(255, 255, 255, 0.3); border-radius: 8px; font-size: 16px; transition: all 0.3s ease; backdrop-filter: blur(10px);">→</button>
        </div>
    </div>
    <style>
        html {{
            background-color: #0e1117;
            font-family: "Source Sans Pro", sans-serif;
        }}
        * {{
            box-sizing: border-box;
        }}
        button:hover {{
            background: rgba(255, 255, 255, 0.3) !important;
            transform: scale(1.05);
        }}
        #decision-display {{
            transition: opacity 0.3s ease;
        }}
    </style>
    <script>
        var decisions = {decisions};
        var currentDecisionIndex = 0;
        var autoRotateDecisionInterval = null;
        
        function updateDecisionDisplay() {{
            var decisionDisplay = document.getElementById('decision-display');
            decisionDisplay.style.opacity = '0';
            setTimeout(function() {{
                decisionDisplay.textContent = decisions[currentDecisionIndex];
                decisionDisplay.style.opacity = '1';
            }}, 150);
            
            document.getElementById('decision-counter').textContent = 'Decision ' + (currentDecisionIndex + 1) + ' of ' + decisions.length;
        }}
        
        function nextDecision() {{
            currentDecisionIndex = (currentDecisionIndex + 1) % decisions.length;
            updateDecisionDisplay();
        }}
        
        function prevDecision() {{
            currentDecisionIndex = (currentDecisionIndex - 1 + decisions.length) % decisions.length;
            updateDecisionDisplay();
        }}
        
        // Start automatic rotation every 5 seconds
        function startAutoRotateDecision() {{
            if (autoRotateDecisionInterval) {{
                clearInterval(autoRotateDecisionInterval);
            }}
            autoRotateDecisionInterval = setInterval(nextDecision, 5000);
        }}
        
        // Start auto-rotation on load
        startAutoRotateDecision();
    </script>
    """
    
    st.components.v1.html(html_code, height=100)
