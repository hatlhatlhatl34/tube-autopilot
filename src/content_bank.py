"""Offline fallback content banks — the pipeline never runs dry, with or without AI.

Each bank backs one channel niche. The AI writer is the primary source; these
guarantee a publishable, on-brand script whenever the API is down or rate-limited.
"""
from __future__ import annotations

import random

# ---------------------------------------------------------------- motivation
QUOTES = [
    ("Discipline is choosing between what you want now and what you want most.", "Abraham Lincoln"),
    ("Success is not final, failure is not fatal: it is the courage to continue that counts.", "Winston Churchill"),
    ("The future depends on what you do today.", "Mahatma Gandhi"),
    ("Don't watch the clock; do what it does. Keep going.", "Sam Levenson"),
    ("It always seems impossible until it's done.", "Nelson Mandela"),
    ("Whether you think you can or you think you can't, you're right.", "Henry Ford"),
    ("The only limit to our realization of tomorrow is our doubts of today.", "Franklin D. Roosevelt"),
    ("Do what you can, with what you have, where you are.", "Theodore Roosevelt"),
    ("Hardships often prepare ordinary people for an extraordinary destiny.", "C.S. Lewis"),
    ("A year from now you may wish you had started today.", "Karen Lamb"),
    ("The best time to plant a tree was 20 years ago. The second best time is now.", "Chinese Proverb"),
    ("You miss 100 percent of the shots you don't take.", "Wayne Gretzky"),
    ("I have not failed. I've just found 10,000 ways that won't work.", "Thomas Edison"),
    ("If you're going through hell, keep going.", "Winston Churchill"),
    ("Energy and persistence conquer all things.", "Benjamin Franklin"),
    ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
    ("Act as if what you do makes a difference. It does.", "William James"),
    ("Quality is not an act, it is a habit.", "Aristotle"),
    ("The secret of getting ahead is getting started.", "Mark Twain"),
    ("Well done is better than well said.", "Benjamin Franklin"),
    ("Perseverance is not a long race; it is many short races one after the other.", "Walter Elliot"),
    ("Courage doesn't always roar. Sometimes it's the quiet voice at the end of the day saying, I'll try again tomorrow.", "Mary Anne Radmacher"),
    ("We are what we repeatedly do. Excellence, then, is not an act but a habit.", "Aristotle"),
    ("Fall seven times, stand up eight.", "Japanese Proverb"),
    ("Everything you've ever wanted is on the other side of fear.", "George Addair"),
    ("Success is the sum of small efforts repeated day in and day out.", "Robert Collier"),
    ("Don't count the days, make the days count.", "Muhammad Ali"),
    ("The man who moves a mountain begins by carrying away small stones.", "Confucius"),
    ("What you get by achieving your goals is not as important as what you become by achieving your goals.", "Zig Ziglar"),
    ("Little by little, one travels far.", "J.R.R. Tolkien"),
    ("Success is walking from failure to failure with no loss of enthusiasm.", "Winston Churchill"),
    ("The road to success and the road to failure are almost exactly the same.", "Colin R. Davis"),
    ("Opportunities don't happen. You create them.", "Chris Grosser"),
    ("Don't be afraid to give up the good to go for the great.", "John D. Rockefeller"),
    ("I find that the harder I work, the more luck I seem to have.", "Thomas Jefferson"),
    ("Success usually comes to those who are too busy to be looking for it.", "Henry David Thoreau"),
    ("The way to get started is to quit talking and begin doing.", "Walt Disney"),
    ("Don't let yesterday take up too much of today.", "Will Rogers"),
    ("If you are working on something that you really care about, you don't have to be pushed. The vision pulls you.", "Steve Jobs"),
    ("Small deeds done are better than great deeds planned.", "Peter Marshall"),
    ("Do what you feel in your heart to be right — for you'll be criticized anyway.", "Eleanor Roosevelt"),
    ("Efforts and courage are not enough without purpose and direction.", "John F. Kennedy"),
    ("Things work out best for those who make the best of how things work out.", "John Wooden"),
    ("A winner is a dreamer who never gives up.", "Nelson Mandela"),
    ("Doubt kills more dreams than failure ever will.", "Suzy Kassem"),
    ("Great things are done by a series of small things brought together.", "Vincent Van Gogh"),
    ("You do not rise to the level of your goals. You fall to the level of your systems.", "James Clear"),
    ("Start where you are. Use what you have. Do what you can.", "Arthur Ashe"),
    ("It's not whether you get knocked down, it's whether you get up.", "Vince Lombardi"),
]

MOTIVATION_THEMES = [
    "discipline", "consistency", "focus", "resilience", "patience", "courage",
    "purpose", "growth", "gratitude", "momentum", "self-belief", "habits",
]

MOTIVATION_HOOKS = [
    "Most people quit right before it works.",
    "Nobody is coming to save you — and that's good news.",
    "One rule separates winners from everyone else.",
    "You don't need motivation. You need this.",
    "Read this before you give up on your goals.",
    "The gap between who you are and who you want to be is smaller than you think.",
    "Your future self is watching you right now.",
    "This is why your habits beat your goals.",
]

MOTIVATION_LESSONS = [
    "Motivation fades in days. Discipline compounds for decades.",
    "Small daily wins beat rare heroic efforts every single time.",
    "You don't rise to your goals. You fall to your systems.",
    "Consistency turns ordinary people into unstoppable ones.",
    "Every rep, every page, every early morning is a vote for who you become.",
    "The pain of discipline is temporary. The pain of regret lasts forever.",
    "Progress hides in the boring days you don't feel like showing up.",
    "Start before you feel ready. Readiness is a byproduct of action.",
    "Your habits decide your future long before your goals do.",
    "Nobody claps for the boring years. They clap for results they can't see the roots of.",
    "Pressure is proof you're in position for something bigger.",
    "The person who shows up tired outperforms the person waiting to feel ready.",
    "Discipline is remembering what you want beyond the moment.",
    "One honest hour beats a whole day of distracted effort.",
    "You don't need a new plan. You need to finish the one you started.",
    "Comparison steals the fuel you need for your own climb.",
]

MOTIVATION_OUTROS = [
    "Save this and reread it tomorrow morning.",
    "Follow for your daily dose of discipline.",
    "One percent better every day. Let's go.",
    "Share this with someone who needs it today.",
]

# ---------------------------------------------------------------------- facts
FACTS = [
    "Honey never spoils. Archaeologists found 3,000-year-old honey in Egyptian tombs that was still edible.",
    "Octopuses have three hearts and blue blood.",
    "A day on Venus is longer than a year on Venus.",
    "Bananas are berries, but strawberries aren't.",
    "There are more possible chess games than atoms in the observable universe.",
    "Sharks existed before trees. Sharks are about 400 million years old; trees around 350 million.",
    "Wombat poop is cube-shaped.",
    "Your brain uses about 20 percent of your body's total energy.",
    "Hot water can freeze faster than cold water. It's called the Mpemba effect.",
    "The Eiffel Tower can grow more than 15 centimeters taller in summer heat.",
    "Scotland's national animal is the unicorn.",
    "A group of flamingos is called a flamboyance.",
    "Human DNA is about 60 percent the same as a banana's.",
    "Lightning strikes the Earth roughly 100 times every second.",
    "There is enough water inside the rings of Saturn to fill 6 percent of the Mediterranean Sea.",
    "The shortest war in history lasted 38 minutes. Britain vs Zanzibar, 1896.",
    "Bubble wrap was originally invented as wallpaper.",
    "A single cloud can weigh over a million pounds.",
    "Ants take around 250 naps a day, each lasting about a minute.",
    "The human body glows faintly. We emit tiny amounts of visible light, too weak for the eye to see.",
    "Cows have best friends and get stressed when separated from them.",
    "The word 'set' has more than 430 different meanings in English, the most of any word.",
    "Pineapples take about two years to grow a single fruit.",
    "Space smells like seared steak and hot metal, according to astronauts.",
    "The total weight of ants on Earth once rivaled the total weight of humans.",
    "Your stomach gets a new lining every few days because stomach acid would otherwise digest it.",
    "The loudest sound ever recorded was the 1883 Krakatoa eruption — heard 4,800 kilometers away.",
    "Some turtles can breathe through their butts for months underwater.",
    "The Moon has moonquakes. They can last up to an hour.",
    "There's a basketball-sized diamond in space. The collapsed star BPM 37093 is essentially a giant cosmic diamond.",
    "You share your birthday with roughly 21 million people around the world.",
    "Butterflies taste with their feet.",
    "If you could fold a piece of paper 42 times, it would reach the Moon.",
    "Sloths can hold their breath longer than dolphins — up to 40 minutes.",
    "The human eye can distinguish about 10 million different colors.",
    "In Switzerland, it's illegal to own just one guinea pig — loneliness is considered animal cruelty.",
    "The average person walks the equivalent of five times around the Earth in a lifetime.",
    "Neutron stars are so dense that a teaspoon would weigh about 6 billion tons.",
    "Caffeine blocks adenosine, the chemical that makes you feel sleepy — tricking your brain into alert mode.",
    "Cleopatra lived closer in time to the Moon landing than to the building of the Great Pyramid.",
    "The Great Wall of China is not visible from the Moon with the naked eye.",
    "Venus spins backwards. On Venus, the Sun rises in the west.",
    "An adult human has fewer bones than a baby — some fuse together as we grow.",
    "The only letter not appearing in any U.S. state name is Q.",
    "Your left lung is smaller than your right — it makes room for your heart.",
    "A shrimp's heart is in its head.",
    "Oxford University is older than the Aztec Empire. Teaching existed there by 1096; the Aztec capital was founded in 1325.",
    "There are more trees on Earth than stars in the Milky Way — about 3 trillion trees versus roughly 100-400 billion stars.",
    "A bolt of lightning is about five times hotter than the surface of the Sun.",
    "Africa sits in all four hemispheres — the only continent that does.",
    "The Sun holds about 99.86 percent of all the mass in the solar system.",
    "Bananas are naturally slightly radioactive from potassium-40 — you'd need millions at once for it to matter.",
    "The deepest part of the ocean, Challenger Deep, is deeper than Mount Everest is tall.",
    "Some metals are so reactive they corrode the instant they touch air — cesium is stored in sealed glass for that reason.",
    "Your sense of smell wires almost directly into the brain's memory center — that's why scents pull memories so fast.",
    "Wombat intestines are unevenly elastic, and that's exactly why their poop comes out cube-shaped.",
    "A day on Mercury, from sunrise to sunrise, lasts about 176 Earth days.",
    "There are more possible arrangements of a shuffled deck of cards than atoms on Earth — by a huge margin.",
    "The first item ever sold on eBay was a broken laser pointer. It sold for 14 dollars and 83 cents.",
]

FACTS_HOOKS = [
    "This sounds fake, but it's 100 percent true.",
    "Number 3 broke my brain.",
    "You won't believe what scientists found.",
    "School never taught us this.",
    "Wait until you hear the last one.",
]

FACTS_OUTROS = [
    "Follow for a new fact every single day.",
    "Which one surprised you most? Comment below.",
    "Save this for your next trivia night.",
    "Share this with the smartest person you know.",
]

# ---------------------------------------------------------------------- tech
TECH_FALLBACK_FACTS = [
    "AI models can now generate a full image in under a second on a phone.",
    "The first computer bug was an actual moth, found inside a Harvard computer in 1947.",
    "Around 90 percent of the world's data was created in just the last few years.",
    "The first smartphone hit the market over 30 years ago, in 1994.",
    "A modern smartwatch has more computing power than the Apollo guidance computer.",
    "GPT-style models read more text in training than any human could read in 20,000 lifetimes.",
    "The Transformer architecture, the engine behind modern AI, was invented in 2017.",
    "The first 1GB hard drive, from 1980, was the size of a refrigerator and cost 40,000 dollars.",
    "More people on Earth have mobile phones than toothbrushes.",
    "The first email spam was sent in 1978 — decades before most people had email.",
    "Undersea fiber cables carry about 99 percent of intercontinental internet traffic.",
    "The first website ever made is still online at info.cern.ch.",
    "Linux runs most of the internet's servers, nearly all supercomputers, and lives inside every Android phone.",
    "The first computer mouse was carved from wood and had one button.",
    "A single modern GPU can do more calculations per second than every computer on Earth combined in the 1990s.",
    "Quantum computers don't replace normal ones — they're built for special problems like simulating molecules.",
    "Self-driving cars use the same family of neural networks that powers voice assistants.",
    "The first text message ever sent said 'Merry Christmas', in 1992.",
    "Bluetooth is named after a 10th-century Danish king, Harald Bluetooth.",
    "Undersea internet cables are reinforced against shark bites — sharks are curious about their electromagnetic fields.",
    "The code that guided Apollo 11 to the Moon had about 145,000 lines — a modern car carries over 100 million.",
    "AI image generators create pictures by learning to remove noise, pixel by pixel.",
    "The first YouTube video was 19 seconds long, filmed at a zoo, in 2005.",
]

TECH_HOOKS = [
    "AI just moved fast again. Here's what matters.",
    "Here's what actually happened in AI today.",
    "Three AI stories you can't afford to miss.",
    "The AI race just changed gear — here's the update.",
]

TECH_OUTROS = [
    "Follow so you never miss an AI update.",
    "Subscribe for tomorrow's AI breakdown.",
    "Tomorrow's AI news lands here. Stay tuned.",
]

# --------------------------------------------------------------------- money
MONEY_RULES = [
    "Pay yourself first. Automate savings before you ever see the money.",
    "The 24-hour rule beats impulse buying: wait a day before any non-essential purchase.",
    "If you can't afford it twice, you can't really afford it once.",
    "Wealth is boring: index funds, patience, and time in the market beat trading.",
    "Every dollar has a job: spend, save, invest, or give — never idle.",
    "Lifestyle creep is the silent killer of raises. Bank the difference instead.",
    "Your emergency fund buys freedom, not just safety — aim for six months of expenses.",
    "The best investment you'll ever make is raising your income skills.",
    "Compound interest is the eighth wonder of the world — but only time unlocks it.",
    "Broke people buy liabilities that look like assets. The rich buy cash-flow.",
    "A 30-minute money date with yourself each week beats a yearly panic.",
    "Track your net worth monthly. What gets measured grows.",
    "No loan for depreciating toys. Debt only for assets that pay you back.",
    "The 50-30-20 rule still works: needs, wants, then invest the fifth of every paycheck.",
    "Rich people buy time. Broke people sell theirs for small discounts.",
    "Never finance a lifestyle on income you haven't earned yet.",
    "Your salary makes you a living; your assets make you free.",
    "Savings without a goal is just delayed spending. Give every dollar a mission.",
    "The stock market transfers money from the impatient to the patient.",
    "If your income rises and your joy doesn't, your spending leaked — find the leak.",
    "Two incomes and one lifestyle is the fastest legal wealth builder for couples.",
    "Buy the boring essentials once, well. Repurchasing cheap junk is the real luxury tax.",
    "A dollar invested at 20 is worth roughly ten at retirement age. Time beats amount.",
    "Debt on consuming drags you down; debt on producing assets can lift you.",
    "The poorest people pay the highest interest — because lenders price desperation.",
    "Automate the boring: autopay bills, auto-invest raises, auto-escalate savings yearly.",
    "If you can't explain the investment in one sentence, don't put your savings in it.",
    "Wealth is what you don't see: it's the car not bought and the upgrade not taken.",
    "Salary grows linearly; skills compound. Invest in the compounding one.",
    "Every subscription is a tiny employee you pay forever — audit them yearly.",
    "Negotiate once, get paid for years: a 10 percent raise at 25 compounds through your whole career.",
    "Money without a budget is like a team without a coach — talent wasted.",
    "Insurance isn't an investment; it's a firewall. Keep the two separate.",
    "The market's best days come right after its worst days — missing them ruins returns.",
    "Cash is optionality: it lets you buy when others are forced to sell.",
    "If a deal requires urgency, the urgency is the scam.",
    "Spend on what you use daily: your bed, your chair, your tools. Skimp on the rest.",
    "Financial freedom number: 25 times your yearly spending. Track your progress toward it, not your neighbor's car.",
]

MONEY_HOOKS = [
    "Schools never taught you this money rule.",
    "The rich follow one rule the broke ignore.",
    "This one shift changes your financial future.",
    "If your money isn't growing, you're breaking this rule.",
    "Read this before your next paycheck.",
]

MONEY_OUTROS = [
    "Follow for one money rule a day.",
    "Save this — your future self will thank you.",
    "Share this with someone building wealth.",
    "Subscribe and take one percent more control of your money.",
]

# ---------------------------------------------------------------------- API
def _pick(items, rng):
    return rng.choice(items)


def _biased(rng, candidates: list[str], style_hint: str | None) -> str:
    """Pick a title, biased toward the audience's winning style."""
    from . import intelligence
    pool = intelligence.reorder_for_style(candidates, style_hint)
    # keep some exploration: 70% pick from the preferred block, 30% anywhere
    if style_hint and len(pool) > 2 and rng.random() < 0.7:
        return rng.choice(pool[: max(1, len(pool) * 2 // 3)])
    return rng.choice(pool)


def motivation_bank(rng: random.Random, style_hint: str | None = None) -> dict:
    quote, author = _pick(QUOTES, rng)
    theme = rng.choice(MOTIVATION_THEMES)
    theme_t = theme.title()   # title-case for titles
    title = _biased(rng, [
        f"{author} Understood This Early",
        f"What {author} Knew About Success",
        f"{author}: Start Before You Feel Ready",
        "Read This If You Feel Stuck In Life",
        f"Why {theme_t} Beats Talent Every Time",
        f"How {theme_t} Rewires Your Brain",
        f"The {theme_t} Rule (Do This For 30 Days)",
        f"Nobody Talks About This {theme_t} Truth",
        f"5 Signs Your {theme_t} Is Working",
        f"This {theme_t} Habit Changes Everything",
    ], style_hint)
    return {
        "hook": rng.choice(MOTIVATION_HOOKS),
        "scenes": [
            f'{quote}',
            f'{author} said that for a reason.',
            rng.choice(MOTIVATION_LESSONS),
            rng.choice(MOTIVATION_LESSONS),
            rng.choice(MOTIVATION_LESSONS),
        ],
        "outro": rng.choice(MOTIVATION_OUTROS),
        "title": title,
        "thumbnail_text": theme.upper() + " RULES",
        "topic": f"{theme} — {author} quote",
    }


def facts_bank(rng: random.Random, topic: str | None = None, style_hint: str | None = None) -> dict:
    picks = rng.sample(FACTS, 5)
    # NOTE: bank facts are general-knowledge — the title must NOT claim they are
    # about a specific trending topic (that claim is only honest for AI-written
    # scripts, which can genuinely address the trend).
    title = _biased(rng, [
        "5 Facts That Sound Fake (But Are 100% True)",
        "Why Nobody Taught You These 5 Facts",
        "5 Facts That Will Break Your Brain",
        "These 5 Facts Sound Impossible — They're Not",
        "5 True Facts You Won't Believe At First",
        "How Is Fact #4 Even Real?",
    ], style_hint)
    return {
        "hook": rng.choice(FACTS_HOOKS),
        "scenes": [f"Fact {i}: {p}" for i, p in enumerate(picks, 1)],
        "outro": rng.choice(FACTS_OUTROS),
        "title": title,
        "thumbnail_text": "5 REAL FACTS",
        "topic": "facts roundup",
    }


def tech_bank(rng: random.Random, headlines: list[str], style_hint: str | None = None) -> dict:
    headlines = headlines[:3] if headlines else []
    scenes = []
    for h in headlines:
        h = h.strip().rstrip(".")
        scenes.append(f"In AI news today: {h}.")
    while len(scenes) < 3:
        scenes.append(f"Quick fact: {rng.choice(TECH_FALLBACK_FACTS)}")
    title = _biased(rng, [
        "3 AI Stories You Missed Today",
        "Why Everyone Is Talking About This AI News",
        "AI Just Changed — Here's What Matters",
        "The AI News You Need Today",
        "5 AI Updates In 40 Seconds",
        "This AI Story Broke Today",
    ], style_hint)
    return {
        "hook": rng.choice(TECH_HOOKS),
        "scenes": scenes,
        "outro": rng.choice(TECH_OUTROS),
        "title": title,
        "thumbnail_text": "AI NEWS DROP",
        "topic": "AI news roundup",
    }


def money_bank(rng: random.Random, style_hint: str | None = None) -> dict:
    title = _biased(rng, [
        "The Money Rule Schools Never Taught You",
        "Why The Rich Don't Save — They Do This Instead",
        "4 Money Rules That Quietly Build Wealth",
        "How Normal People Get Rich (Slowly)",
        "This Money Habit Beats Luck Every Time",
        "The 1% Money Rule Nobody Uses",
    ], style_hint)
    return {
        "hook": rng.choice(MONEY_HOOKS),
        "scenes": [
            rng.choice(MONEY_RULES),
            rng.choice(MONEY_RULES),
            rng.choice(MONEY_RULES),
            rng.choice(MONEY_RULES),
        ],
        "outro": rng.choice(MONEY_OUTROS),
        "title": title,
        "thumbnail_text": "MONEY RULE",
        "topic": "money rules",
    }
