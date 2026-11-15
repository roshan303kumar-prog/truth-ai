"""
Seed script to populate initial demo data for demonstration & academic presentation.
"""
from datetime import datetime, timezone, timedelta
from app import create_app
from database import db
from database.models import User, VerificationReport, UserSettings, UserReview

app = create_app()

def seed():
    with app.app_context():
        db.create_all()

        # Create demo user if not exists
        demo_user = User.query.filter_by(username="demo_user").first()
        if not demo_user:
            demo_user = User(
                username="demo_user",
                email="demo@truth-ai.org",
                full_name="Alex Rivera (Researcher)",
                created_at=datetime.now(timezone.utc) - timedelta(days=14),
            )
            demo_user.set_password("TruthAI@2026")
            db.session.add(demo_user)
            db.session.flush()

            settings = UserSettings(user_id=demo_user.id)
            db.session.add(settings)
            print("Created demo user: 'demo_user' / 'TruthAI@2026'")

        # Create sample reports if none exist
        if VerificationReport.query.count() == 0:
            reports_data = [
                {
                    "user_id": demo_user.id,
                    "verification_type": "news",
                    "title_or_claim": "NASA James Webb Space Telescope reveals earliest known distant galaxies in deep space",
                    "submitted_content": "NASA's James Webb Space Telescope (JWST) NIRCam instruments captured candidate galaxies dating back 350 million years after the Big Bang.",
                    "verdict": "Supported by available evidence",
                    "confidence_score": 92.0,
                    "explanation": "Multiple peer-reviewed astrophysical releases and NASA/ESA official mission archives confirm the observation of high-redshift early galaxies.",
                    "supporting_evidence": [
                        {
                            "title": "NASA's Webb Discovers Earliest Galaxies in Early Universe",
                            "snippet": "Observations from the James Webb Space Telescope's NIRCam instruments confirmed spectroscopic redshift measurements for candidate early galaxies.",
                            "url": "https://www.nasa.gov/mission_pages/webb/main/index.html",
                            "source": "NASA Press Archive",
                            "published_date": "2023-01-14",
                            "rating": "Verified",
                            "stance": "supports"
                        }
                    ],
                    "contradicting_evidence": [],
                    "limitations": [
                        "Spectroscopic confirmations for the most distant galaxies are continuously updated as more observational deep-field cycles are completed."
                    ],
                    "source_links": [
                        {"title": "NASA Webb Science Mission", "url": "https://www.nasa.gov/mission_pages/webb/main/index.html", "publisher": "NASA"}
                    ],
                    "is_saved": True,
                    "created_at": datetime.now(timezone.utc) - timedelta(days=3),
                },
                {
                    "user_id": demo_user.id,
                    "verification_type": "news",
                    "title_or_claim": "COVID-19 vaccines contain secret 5G microchips for citizen tracking",
                    "submitted_content": "Social media viral posts claim that mRNA vaccines contain microscopic RFID hardware that interacts with 5G towers.",
                    "verdict": "False or contradicted by reliable evidence",
                    "confidence_score": 95.0,
                    "explanation": "Extensive international laboratory chemical analysis and regulatory documentation unequivocally confirm vaccine solutions contain mRNA, lipids, and salts with zero electronic microhardware.",
                    "supporting_evidence": [],
                    "contradicting_evidence": [
                        {
                            "title": "WHO Fact Check: Vaccine Ingredients & Microelectronics",
                            "snippet": "Biochemical breakdowns by independent laboratories across 100+ countries confirm no digital tracking hardware exists in pharmaceutical vaccines.",
                            "url": "https://www.who.int",
                            "source": "World Health Organization",
                            "published_date": "2021-04-10",
                            "rating": "False",
                            "stance": "refutes"
                        }
                    ],
                    "limitations": [
                        "Public health misinformation often re-emerges with altered buzzwords across private messaging apps."
                    ],
                    "source_links": [
                        {"title": "WHO Fact Check", "url": "https://www.who.int", "publisher": "World Health Organization"}
                    ],
                    "is_saved": True,
                    "created_at": datetime.now(timezone.utc) - timedelta(days=2),
                },
                {
                    "user_id": demo_user.id,
                    "verification_type": "news",
                    "title_or_claim": "Eating raw garlic completely cures any bacterial infection in 24 hours",
                    "submitted_content": "A viral wellness blog asserts that consuming crushed garlic eliminates all pathogenic bacteria faster than prescribed antibiotics.",
                    "verdict": "Misleading or missing context",
                    "confidence_score": 74.0,
                    "explanation": "While allicin in fresh garlic exhibits mild in-vitro antimicrobial properties in laboratory petri dishes, clinical human trials show it cannot replace systemic antibiotics for acute bacterial infections.",
                    "supporting_evidence": [],
                    "contradicting_evidence": [
                        {
                            "title": "Medical Evaluation of Dietary Antimicrobial Claims",
                            "snippet": "In-vitro antimicrobial activity of dietary compounds does not equate to effective systemic clinical treatment of acute bacterial infections in patients.",
                            "url": "https://www.nih.gov",
                            "source": "National Institutes of Health (NIH)",
                            "published_date": "2022-08-20",
                            "rating": "Misleading Context",
                            "stance": "refutes"
                        }
                    ],
                    "limitations": [
                        "Dietary health claims frequently distort in-vitro laboratory studies into unverified medical treatments."
                    ],
                    "source_links": [
                        {"title": "NIH Clinical Studies", "url": "https://www.nih.gov", "publisher": "NIH"}
                    ],
                    "is_saved": False,
                    "created_at": datetime.now(timezone.utc) - timedelta(hours=18),
                },
                {
                    "user_id": demo_user.id,
                    "verification_type": "image",
                    "title_or_claim": "Photo Analysis: suspicious_celebrity_scandal.jpg",
                    "submitted_content": "Uploaded photograph scrutinized for facial boundary splicing and generative AI diffusion artifacts.",
                    "verdict": "False or contradicted by reliable evidence",
                    "confidence_score": 88.0,
                    "explanation": "High Error Level Analysis variance (max diff 42) and detected ComfyUI diffusion generation parameters in embedded metadata confirm synthetic creation.",
                    "supporting_evidence": [],
                    "contradicting_evidence": [],
                    "limitations": [
                        "AI generative model detection is probabilistic and must be paired with reverse image indexing."
                    ],
                    "source_links": [
                        {"title": "TinEye Visual Search", "url": "https://tineye.com", "publisher": "TinEye"}
                    ],
                    "is_saved": True,
                    "created_at": datetime.now(timezone.utc) - timedelta(hours=6),
                }
            ]

            for rd in reports_data:
                rep = VerificationReport(
                    user_id=rd["user_id"],
                    verification_type=rd["verification_type"],
                    title_or_claim=rd["title_or_claim"],
                    submitted_content=rd["submitted_content"],
                    verdict=rd["verdict"],
                    confidence_score=rd["confidence_score"],
                    explanation=rd["explanation"],
                    is_saved=rd["is_saved"],
                    created_at=rd["created_at"],
                )
                rep.supporting_evidence = rd["supporting_evidence"]
                rep.contradicting_evidence = rd["contradicting_evidence"]
                rep.limitations = rd["limitations"]
                rep.source_links = rd["source_links"]
                db.session.add(rep)

            db.session.commit()
            print(f"Seeded {len(reports_data)} demo verification reports successfully!")
        else:
            print("Database already contains verification records.")

        # Seed initial reviews if none exist
        if UserReview.query.count() == 0:
            demo_reviews = [
                UserReview(
                    user_name="Priya Sharma",
                    user_role="Journalism Student",
                    rating=5,
                    title="Game changer for verifying viral WhatsApp claims!",
                    review_text="The Link Scanner and NEO Assistant are incredible. I pasted a suspicious SBI KYC SMS link and it immediately warned me of brand impersonation with 92% risk score.",
                    is_approved=True,
                    created_at=datetime.now(timezone.utc) - timedelta(days=3),
                ),
                UserReview(
                    user_name="Vikram Malhotra",
                    user_role="Cybersecurity Researcher",
                    rating=5,
                    title="Outstanding Error Level Analysis & Forensics",
                    review_text="The ELA heatmap and optical metadata audit accurately showed localized compression discrepancies on photoshopped identity documents. Very impressed.",
                    is_approved=True,
                    created_at=datetime.now(timezone.utc) - timedelta(days=6),
                ),
                UserReview(
                    user_name="Ananya Deshmukh",
                    user_role="Digital Fact Checker",
                    rating=5,
                    title="NEO AI Assistant is fast, intelligent & screen-aware",
                    review_text="Being able to share my screen and have NEO point out exactly where to click and what errors exist makes this platform so seamless.",
                    is_approved=True,
                    created_at=datetime.now(timezone.utc) - timedelta(days=8),
                ),
                UserReview(
                    user_name="Rohit Verma",
                    user_role="Verified Citizen",
                    rating=4,
                    title="Love the Female/Male voice narration feature!",
                    review_text="I don't always have time to read long technical reports. The AI Voice narration explains whether a claim is real or fake in seconds.",
                    is_approved=True,
                    created_at=datetime.now(timezone.utc) - timedelta(days=12),
                ),
            ]
            for rev in demo_reviews:
                db.session.add(rev)
            db.session.commit()
            print("Seeded demo user reviews successfully!")

if __name__ == "__main__":
    seed()
