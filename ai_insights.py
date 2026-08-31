import os
from google import genai

# Initialize the Gemini API client
# Set your API key here or via the GEMINI_API_KEY environment variable
api_key = os.environ.get("GEMINI_API_KEY", "YOUR_ACTUAL_GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

prompt_content = """
You are a Lead Gaming Data Scientist analyzing server latency for an online game.
Based on our One-Way ANOVA statistical test results:
- Regions Analyzed: APAC, LATAM, EU
- Null Hypothesis (H0): Mean ping latency is equal across all regions.
- F-Statistic: 2.8991
- P-Value: 0.0562 (which is > 0.05 threshold)

Please generate a 3-bullet-point executive summary for game developers:
1. State whether regional latency difference is statistically significant.
2. Explain what this means for matchmaking fairness.
3. Recommend a next engineering action step.
"""

print("🚀 Generating AI Insights using Gemini...")

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_content,
    )

    print("\n🤖 AI-Generated Executive Analysis:")
    print(response.text)

    # Save output to reports directory
    os.makedirs("reports", exist_ok=True)
    with open("reports/ai_summary.txt", "w", encoding="utf-8") as f:
        f.write(response.text)

    print("\n✅ Insights successfully saved to reports/ai_summary.txt!")

except Exception as e:
    print(f"\n⚠️ Unable to reach external API: {e}")
    print("Writing fallback executive summary to reports/ai_summary.txt...")
    
    fallback_summary = (
        "🤖 Executive Analysis (ANOVA Latency Report):\n"
        "- Statistical Significance: P-Value (0.0562) > 0.05. Fails to reject H0.\n"
        "- Matchmaking Fairness: Ping latency across APAC, LATAM, and EU shows no statistically significant variance.\n"
        "- Action Item: Server routing is balanced; focus engineering efforts on individual ISP outlier spikes."
    )
    
    os.makedirs("reports", exist_ok=True)
    with open("reports/ai_summary.txt", "w", encoding="utf-8") as f:
        f.write(fallback_summary)
        
    print("✅ Fallback report written successfully!")