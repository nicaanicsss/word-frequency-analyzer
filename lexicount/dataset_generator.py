"""Create test datasets of a given size, completely offline.

Two sources of text:
  1. If data/seed.txt exists (for example a Project Gutenberg book you placed
     there yourself), it is repeated until the target size is reached.
  2. Otherwise realistic English-like text is generated from a built-in
     vocabulary of ~2,000 common English words. Words are drawn with a Zipf
     distribution (a few words are very common, most are rare, just like real
     language) and mixed with capitalization, punctuation, contractions and
     line breaks. random.seed(42) makes every run produce identical files.

Usage:
    python dataset_generator.py 1 10 50 100 500      # sizes in MB
"""

import argparse
import os
import random
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
SEED_FILE = os.path.join(DATA_DIR, "seed.txt")
MB = 1024 * 1024
ZIPF_EXPONENT = 1.07     # typical value measured for English text
SENTENCE_POOL_SIZE = 40_000
WRITE_BLOCK_SENTENCES = 2_000

# --- Built-in vocabulary (roughly ordered from most to least common) ---------

FUNCTION_WORDS = """
the of and to a in is it you that he was for on are with as i his they be at one
have this from or had by not but what some we can out other were all there when up
your how said an each she which do their if will way about many then them would so
these her him has more could no my than who may been now any only our me just very
also much too same even here such why again off well still both while because
through over under before after above between into during without within along
across behind beyond near around against among since until upon however although
though yet once never always often sometimes usually perhaps maybe really quite
almost already enough rather soon later today tonight tomorrow yesterday everyone
everything someone something nothing nobody anyone anything another every few
several most must should shall might us those whose whom where yes am does did
done got went made took saw came thought gave found told knew felt left kept began
ran brought wrote sat stood lost paid met led heard held understood become became
being having going doing known given taken seen written
"""

CONTRACTIONS = """
don't it's i'm can't won't you're that's isn't didn't we're they're i've let's
there's doesn't wasn't couldn't wouldn't i'll she's he's aren't haven't we'll
"""

IRREGULAR_WORDS = """
man men woman women child children people person life lives foot feet tooth mouse
know take see come think give tell feel leave keep begin run bring write sit stand
lose pay meet lead understand hold become make go get say find fall grow throw
speak break choose drive eat drink fly forget hide ride ring rise shake sing sleep
steal swim teach wake wear win buy catch fight seek sell send spend build
"""

REGULAR_VERBS = """
look want use work seem try call ask help talk turn start show play move like live
believe happen provide include continue learn change follow create allow add
appear wait serve expect stay reach remain suggest raise pass require report decide
pull return explain hope develop carry receive agree support produce cover point
listen realize place close involve increase finish fill visit wish enjoy travel
answer jump laugh smile dream study climb push dance paint clean cook wash pick
count share save join reply rest test check form fix mark miss name order prefer
prepare protect prove walk open watch remember love consider offer need kill end
discover describe imagine notice decide manage measure mention pick plant pour
pray print reduce relax rely repeat replace rescue respect search settle shout
sign solve sort sound spell spray squeeze stamp stare state step store suffer
supply surround suspect taste thank touch train treat trust type value vanish
wander warn waste welcome whisper wonder worry yell accept achieve admire admit
advise afford arrange arrive attach attack attempt attend avoid bake balance
bathe behave belong blink boil borrow bounce breathe brush burn calculate care
cause celebrate challenge charge chase cheer collect combine comfort compare
complain complete concern confess connect contain copy correct cough crash crawl
cross crowd cure damage deliver depend deserve destroy disappear divide doubt
earn educate employ encourage escape examine exercise exist explore express
fasten fear fetch float flow fold force frighten gather glow greet guess guide
hammer hand handle harm hate heat hunt hurry identify ignore improve inform
inject inspect intend interest introduce invent invite kick kiss knock last
launch level lift limit load lock march marry matter melt mix murmur obey observe
obtain occur own pack park perform permit phone pinch please polish possess post
practice present press pretend prevent promise provide punish purchase question
race rain reach record refuse regret reject release remove rent repair request
rush scratch scream serve shiver sail sniff snow spark spill sprout squash
"""

NOUNS = """
time year day thing world hand part place case week company system program
question government number night point home water room mother area money story
fact month lot right study book eye job word business issue side kind head house
service friend father power hour game line end member law car city community name
president team minute idea body information back parent face level office door
health art war history party result change morning reason research girl guy
moment air teacher force education student problem family group country school
state month bank market street garden river mountain forest island ocean village
road bridge window table chair bed kitchen floor wall picture letter paper pen
pencil computer phone screen machine engine train plane boat ship bird animal
horse dog cat flower tree plant seed field farm color song music sound voice
language question answer lesson class subject science nature planet star moon
sun cloud storm wind summer winter spring autumn season week weekend holiday
birthday dinner breakfast lunch meal bread apple orange egg cake coffee drink
shirt dress shoe hat coat bag box bottle cup plate spoon fork knife key lock
gate fence hill valley lake beach desert road path journey trip adventure
dream memory thought feeling hope fear joy anger love peace freedom truth
secret mystery plan goal choice chance mistake success failure victory battle
army soldier king queen prince princess castle tower kingdom empire leader
doctor nurse hospital patient medicine farmer worker driver writer artist
singer player captain pilot officer police judge lawyer manager owner customer
neighbor stranger visitor guest brother sister daughter son uncle aunt cousin
husband baby boy friend partner client stone rock metal gold silver iron glass
wood fire light shadow corner edge center circle square shape size weight
height length distance speed direction minute second hour decade century
moment period event meeting conference report record message signal network
website video image photo camera film movie theater show program episode
chapter page sentence paragraph library museum gallery temple church market
shop store restaurant hotel airport station office factory building apartment
room hall stair roof ground surface bottom top middle detail example method
process practice theory model pattern structure rule reason purpose effect
cause source value price cost profit budget account tax income salary job
career skill talent ability habit hobby sport match race goal score prize
gift ticket card note list map clock watch radio lamp candle mirror picture
blanket pillow towel soap brush comb ring necklace button pocket wallet
"""

ADJECTIVES = """
good new first last long great little own other old right big high different
small large next early young important few public bad same able best better
sure free true whole real full special easy clear recent certain personal open
red difficult available likely short single medical current wrong private past
foreign fine common poor natural significant similar hot dead central happy
serious ready simple left physical general environmental financial blue
democratic dark various entire close legal religious cold final main green nice
huge popular traditional cultural strong white black brown yellow quiet loud
bright soft hard gentle kind brave proud calm busy lazy clever smart wise silly
strange famous rich empty heavy light fresh warm cool deep wide narrow thin
thick sweet bitter sour salty delicious beautiful pretty ugly tall tiny giant
ancient modern quick slow rapid sudden careful honest polite angry sad lonely
excited tired hungry thirsty sick healthy safe dangerous wild friendly lucky
curious nervous gentle silent noisy smooth rough sharp clean dirty wet dry
"""


def unique_words(text: str) -> list[str]:
    """Split a word block into a list, removing duplicates but keeping order."""
    return list(dict.fromkeys(text.split()))


def plural(noun: str) -> str:
    """Very small English plural rule set (box -> boxes, city -> cities)."""
    if noun.endswith(("s", "x", "ch", "sh")):
        return noun + "es"
    if noun.endswith("y") and noun[-2] not in "aeiou":
        return noun[:-1] + "ies"
    return noun + "s"


def verb_forms(verb: str) -> list[str]:
    """Return -s, -ed and -ing forms of a regular verb (walk -> walks, walked, walking)."""
    if verb.endswith("e"):
        return [verb + "s", verb + "d", verb[:-1] + "ing"]
    if verb.endswith("y") and verb[-2] not in "aeiou":
        return [verb[:-1] + "ies", verb[:-1] + "ied", verb + "ing"]
    if verb.endswith(("s", "x", "ch", "sh")):
        return [verb + "es", verb + "ed", verb + "ing"]
    return [verb + "s", verb + "ed", verb + "ing"]


def build_vocabulary() -> list[str]:
    """Return ~2,000 words, most common first (rank order matters for Zipf)."""
    verbs = unique_words(REGULAR_VERBS)
    nouns = unique_words(NOUNS)
    words = (unique_words(FUNCTION_WORDS) + unique_words(CONTRACTIONS)
             + unique_words(IRREGULAR_WORDS) + verbs + nouns + unique_words(ADJECTIVES))
    for verb in verbs:
        words += verb_forms(verb)
    words += [plural(noun) for noun in nouns]
    return list(dict.fromkeys(words))


def zipf_weights(count: int) -> list[float]:
    """Cumulative Zipf weights: the word of rank r gets weight 1 / r^s."""
    cumulative, running = [], 0.0
    for rank in range(1, count + 1):
        running += 1 / rank ** ZIPF_EXPONENT
        cumulative.append(running)
    return cumulative


def make_sentence(vocabulary: list[str], cum_weights: list[float]) -> str:
    """Build one sentence: capitalized, with optional commas and end punctuation."""
    words = random.choices(vocabulary, cum_weights=cum_weights, k=random.randint(4, 18))
    if random.random() < 0.3:  # add a comma somewhere in the middle
        position = random.randrange(1, len(words))
        words[position - 1] += ","
    words[0] = words[0].capitalize()
    ending = random.choices([".", "?", "!", ";", "..."], weights=[80, 8, 6, 3, 3])[0]
    return " ".join(words) + ending


def build_sentence_pool(vocabulary: list[str]) -> list[str]:
    """Pre-build many distinct sentences so large files can be written quickly."""
    cum_weights = zipf_weights(len(vocabulary))
    return [make_sentence(vocabulary, cum_weights) for _ in range(SENTENCE_POOL_SIZE)]


def make_block(sentence_pool: list[str]) -> str:
    """Join random sentences into lines and paragraphs."""
    parts = []
    for sentence in random.choices(sentence_pool, k=WRITE_BLOCK_SENTENCES):
        separator = random.choices([" ", "\n", "\n\n"], weights=[70, 22, 8])[0]
        parts.append(sentence + separator)
    return "".join(parts)


def write_generated_text(path: str, target_bytes: int) -> None:
    """Write Zipf-distributed English-like text until exactly target_bytes."""
    random.seed(42)  # reproducible: same files on every machine and run
    sentence_pool = build_sentence_pool(build_vocabulary())
    written = 0
    with open(path, "wb") as file:
        while written < target_bytes:
            block = make_block(sentence_pool).encode("ascii")
            block = block[: target_bytes - written]  # trim the final block
            file.write(block)
            written += len(block)


def write_replicated_seed(path: str, target_bytes: int) -> None:
    """Repeat data/seed.txt until exactly target_bytes."""
    with open(SEED_FILE, "rb") as file:
        seed = file.read()
    if not seed:
        raise ValueError(f"{SEED_FILE} is empty")
    seed += b"\n"  # make sure the last word of one copy never joins the next copy
    written = 0
    with open(path, "wb") as file:
        while written < target_bytes:
            block = seed[: target_bytes - written]
            file.write(block)
            written += len(block)


def dataset_path(size_mb: float) -> str:
    """Return data/dataset_<size>MB.txt (e.g. dataset_100MB.txt, dataset_0.5MB.txt)."""
    return os.path.join(DATA_DIR, f"dataset_{size_mb:g}MB.txt")


def generate_dataset(size_mb: float, force: bool = False) -> str:
    """Create a dataset of size_mb megabytes (if not already present) and return its path."""
    if size_mb <= 0:
        raise ValueError("dataset size must be greater than 0 MB")
    os.makedirs(DATA_DIR, exist_ok=True)
    path = dataset_path(size_mb)
    target_bytes = int(size_mb * MB)
    if not force and os.path.isfile(path) and os.path.getsize(path) == target_bytes:
        return path  # already generated: reuse it

    source = "seed.txt replication" if os.path.isfile(SEED_FILE) else "Zipf generator"
    print(f"Generating {path} ({size_mb:g} MB, {source}) ...", flush=True)
    if os.path.isfile(SEED_FILE):
        write_replicated_seed(path, target_bytes)
    else:
        write_generated_text(path, target_bytes)
    return path


def main() -> int:
    """Command-line interface: generate one or more dataset sizes."""
    parser = argparse.ArgumentParser(description="Generate LexiCount test datasets (offline).")
    parser.add_argument("sizes", nargs="*", type=float, default=[1, 10, 50, 100, 500],
                        help="dataset sizes in MB (default: 1 10 50 100 500)")
    parser.add_argument("--force", action="store_true", help="regenerate even if the file exists")
    args = parser.parse_args()
    try:
        for size in args.sizes:
            path = generate_dataset(size, args.force)
            print(f"Ready: {path} ({os.path.getsize(path) / MB:.1f} MB)")
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Vocabulary size of the built-in generator: {len(build_vocabulary())} words")
    return 0


if __name__ == "__main__":
    sys.exit(main())
