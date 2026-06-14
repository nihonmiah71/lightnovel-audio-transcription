# Disclaimer

The python scripts will probably not run on your system unless you installed all the right packages, some of them might only be supported for older pyhton versions (Python 3.12), debug with AI and install the required packages as needed.

# Project Documentation: Audio-Text Alignment and Subtitle Generation Pipeline

## Workflow Overview

1. **Acquire the Source Material**
    * Get the EPUB file of a light novel (for example on Z-Library or by purchasing it). *Please purchase an original copy either way to support the creator and the industry.*

2. **Extract the Text**
    * Load the light novel on Tsuu Reader.
    * Get the HTML text with an addon, for example, the **HTML Copy** addon on the Chrome Web Store: [HTML Copy](https://chromewebstore.google.com/detail/html-copy/mkneclfoofncoidopgeiphnjnpcjelia).

3. **Prepare Audio and Text Pairs**
    * Prepare the HTML text with the Python script (`htmltorawtext.py`) so you only have the raw text.
    * Manually or with the help of a program, assign the text to the audio. You have to make sure that there is no text that does not occur in the audio, and also the other way around: no audio that does not occur in the text.
    * In this case, you have to manually cut the audio with a helper program like **LosslessCut** ([GitHub Repository](https://github.com/mifi/lossless-cut)). 
    * *Example scenario:* You downloaded the whole book HTML and now have raw text for the book, but the audio is separated into chapters or subchapters. You have to combine the subchapters into one chapter and then separate the large text file into smaller text files that only contain the respective chapters. Also, you have to cut off the audio because between chapters a text element is read which in the HTML is saved as a picture.

4. **Generate Subtitles**
    * Create the subtitle file (`.ass` format). Depending on your PC and the length of the audio, this can take a long time. For example, running the program that transcribed the *Oregairu* light novel took approximately 5 minutes per chapter (~170 chapters), totaling around 15 hours.
    * Use the script `rawtexttosubtitlealignment.py` for this step.

5. **Verify and Repair Alignment via Logs**
    * Check if the transcription was successful by inspecting the logs. In order not to read all the logs manually, you should use the `loganalysis.py` script.
    * Go to the corrupted respective `_ai_raw.json` file and modify it surgically. Usually, there is a block where the alignment breaks off. Identify this block in the JSON file and take the respective original text.
    * Format this text segment using an AI with the prompt: 
      > "Remove all quotation marks, brackets, and line breaks from the following Japanese text, and merge it into a single line without changing any words."
    * Insert the formatted text back into the block where the alignment went astray in the previous run.
    * Launch either the `manualaligncorrection.py` or the more verbose `manualaligncorrectionplusfeedback.py` script and choose the file you just modified. 
    * After the correction is complete, you can run `loganalysis.py` again and repeat this loop until all corrupted files are successfully repaired.

6. **Playback**
    * In order to run the subtitle file and your audio at the same time, open the audio file in **mpv player** and then drag the subtitle file directly into the player window.
    * You can also create playlists. An example configuration is linked here: [Oregairu-LightnovelAudio- GitHub](https://github.com/nihonmiah71/Oregairu-LightnovelAudio-).

---

## 1. htmltorawtext.py

### Input / Output Perspective
* **Execution Environment:** The script uses relative paths and is bound to the current working directory. It must be executed within the same folder where the input file resides.
* **Input Files & Location:** Expects a file with the exact name `nani.txt` located in the same directory as the script.
* **Output Files & Location:** Creates a file named exactly `nur_matches.txt` in the same directory.
* **Concrete Input Format:** 
    * A UTF-8 encoded text or HTML file.
    * Content must contain Japanese text segments wrapped inside paragraph tags: `<p>...</p>` or `<p class="middle-block">...</p>`.
    * Frequently contains Japanese Furigana phonetic annotations via `<ruby><rb>Kanji</rb><rt>Furigana</rt></ruby>`.

### Technical Documentation
* **Functionality:** This script parses a text or HTML file containing Japanese text encapsulated inside paragraph tags. It filters out Japanese phonetic guides (Furigana) and any remaining HTML tags to compile a clean, line-separated text file of the narrative content.
* **Operation:** 
    1. Place the target file named `nani.txt` in the same directory as the script.
    2. Execute the script using a Python interpreter (`python htmltorawtext.py`).
    3. The script processes the text and prints a confirmation message indicating the number of successful matches saved into `nur_matches.txt`.
* **Logic:** 
    * **Extraction:** It runs a regular expression (`<p(?: class="middle-block")?>(.+?)</p>`) using `re.findall` with the `re.DOTALL` flag to capture everything inside the paragraph blocks, even if spanning multiple lines.
    * **Furigana Removal:** Inside each matched block, it uses `re.sub` to completely purge `<rt>...</rt>` and optional `<rp>...</rp>` tags along with their internal text content. This removes the phonetic reading layers entirely, leaving only the base Kanji/Kana words.
    * **Tag Stripping:** It targets any remaining structural tags with a generic HTML tag removal regex (`<.*?>`) and writes the stripped text to the output file.
* **Special Elements and Ideas:** 
    * **Multi-Stage Subtitle Preparation:** This program serves as a critical pre-processing layer. Audio alignment systems fail or perform poorly when trying to match structural HTML layout fields or secondary reading keys (Furigana) against raw speech. Removing the readings while keeping the base characters guarantees clean text matching.

---

## 2. loganalysis.py

### Input / Output Perspective
* **Execution Environment:** The script is not tied to a fixed directory location. It can be initialized from anywhere and interactively prompts the user for a target path.
* **Input Files & Location:** Searches recursively (through all subfolders) within the provided target directory for any files ending with the name `mapping_log.txt`.
* **Output Files & Location:** No physical output files are written to the disk. All analysis metrics and validation reports are output directly to the standard output (console/terminal).
* **Concrete Input Format:** 
    * UTF-8 or plain-text log files.
    * The script parses specific structural patterns documenting the alignment engine's state. It expects lines matching the regular expression `Methode:\s*(FUZZY\s*\(OK\)|LOOP_RECOVERY_FALLBACK|DELETION_STRETCH)` (e.g., `Methode: FUZZY (OK)`).

### Technical Documentation
* **Functionality:** This utility traverses a directory structure to look for sync engine outputs (`*mapping_log.txt`). It aggregates performance metrics concerning which alignment algorithms were triggered, calculating success percentages to help identify layout or transcription anomalies.
* **Operation:** 
    1. Run the script.
    2. Enter the absolute or relative path to the directory containing your logs when prompted. Pressing Enter without input defaults to the current working directory.
    3. The script systematically evaluates every log file found and outputs statistical reviews directly onto the terminal.
* **Logic:** 
    * **Recursive Traversal:** Uses `os.walk` to find any file ending with `mapping_log.txt`.
    * **Pattern Matching:** It checks every line using a pre-compiled regular expression looking for strings indicating alignment modes: `FUZZY (OK)`, `LOOP_RECOVERY_FALLBACK`, or `DELETION_STRETCH`.
    * **Statistical Calculation:** For each file, counters increment based on the category. Once a log file analysis finishes, it calculates percentages relative to the total block count.
* **Special Elements and Ideas:** 
    * **Automated Quality Assurance:** The script implements an automated heuristic fallback warning: `[!] WARNING: PLEASE CHECK (FUZZY (OK) is below 80%)`. If the optimal fuzzy alignment falls below this threshold, it flags the file for manual intervention, indicating that the automatic synchronization encountered significant segment deviations or dropouts.

---

## 3. rawtexttosubtitlealignment.py / align87.py

### Input / Output Perspective
* **Execution Environment:** Highly flexible deployment parameters. Features a batch processing design tied to a hardcoded configuration variable (`BASE_PATH`), alongside a single-file processing fallback utilizing cross-platform graphical user interface (GUI) windows.
* **Input Files & Location:** 
    * *Batch Mode:* Automatically targets the folder path configured in `BASE_PATH`, looking for matching pairs of audio and text files sharing identical base filenames.
    * *Single File Mode:* Spawns two consecutive `tkinter` file-selection dialogue prompts, allowing the operator to freely navigate and link any audio file and text file from the filesystem.
* **Output Files & Location:** All generated files are compiled directly within the source directory of the input files, sharing the identical baseline filename prefix:
    * `{basename}.txt`: The finalized text file synced with exact audio time markers.
    * `{basename}_ai_raw.json`: The unprocessed transcription payload directly exported from WhisperX.
    * `{basename}.ass`: The finalized, styled Advanced SubStation Alpha subtitle file.
    * `{basename}_mapping_log.txt`: A granular, step-by-step diagnostic sync log.
    * `{basename}_mapping_details.json`: Structured mapping arrays formatted in JSON.
* **Concrete Input Format:** 
    * *Audio:* Any multimedia audio containers supported natively by WhisperX backend instances (typically `.m4a`, `.mp3`, or `.wav`).
    * *Text:* A clean UTF-8 encoded text document (`.txt`) containing the master script split line-by-line or block-by-block via standard line breaks.

### Technical Documentation
* **Functionality:** This is a comprehensive, automated audio-text alignment pipeline. It utilizes WhisperX to transcribe audio, converts both the transcription and the native script into uniform phonetic streams (Hiragana), maps the text blocks to precise audio timestamps using fuzzy string matching, and outputs an advanced `.ass` subtitle file.
* **Operation:** 
    * *Batch Mode:* Set the `BASE_PATH` variable inside the configuration section to your target folder. The script will automatically pair `.m4a` and `.txt` files sharing identical names.
    * *Single File Mode:* If the batch configurations are bypassed or file structures vary, the user selects individual audio and text documents sequentially via graphical file windows.
* **Logic:** 
    1. **Transcription:** Leverages WhisperX to perform speech-to-text, providing character-level or segment-level timestamps.
    2. **Phonetic Normalization:** Converts both the text script blocks and WhisperX's transcription string into pure Hiragana using `pykakasi`. It strips all punctuation, Kanji, and Latin characters to create a continuous phonetic timeline comparison matrix.
    3. **Two-Way Search Matrix:**
        * **FUZZY (OK):** Tries to find the script block in a local search window of the audio timeline using `difflib.SequenceMatcher`.
        * **LOOP_RECOVERY_FALLBACK:** If a match fails, it expands the search scope forward to catch up with the audio timeline.
        * **DELETION_STRETCH:** If the script contains lines skipped by the speaker or missed by the transcriber, it linearizes the time offsets between the last known valid timestamp and the next successful future anchor match.
    4. **Subtitle Structuring:** Passes the mapped data to `txt_to_ass` to build formatting layers.
* **Special Elements and Ideas:** 
    * **Dynamic Visual Pacing (5-Block Subtitles):** Instead of standard single-line subtitle switching, this program creates a dynamic scroll containing 5 contextual blocks simultaneously on screen. It highlights the current active block with a dot prefix (`●`) and renders a live, per-second countdown timer in the top corner (`Style: Timer`), keeping past and future text segments visible for immersive reading and speech synchronization tracking.

---

## 4. manualaligncorrection.py

### Input / Output Perspective
* **Execution Environment:** Operates independently of its own file layout. It builds an interactive graphical environment via `tkinter` to safely navigate the directory structures.
* **Input Files & Location:** 
    * The user selects a specific WhisperX JSON export file, which must strictly conform to the naming format `*_ai_raw.json`.
    * The corresponding raw script file (`{basename}.txt`) must reside in the **same** directory. If the script file is missing, the application safely halts execution.
* **Output Files & Location:** Generates or updates files directly inside the origin directory where the source JSON file is stored:
    * `{basename}.ass`: A newly compiled, left-aligned SubStation Alpha subtitle track.
    * Automatically synchronizes the timeline entries embedded within the mapped raw text file.
* **Concrete Input Format:** 
    * *JSON Structure:* A native structured JSON output from WhisperX containing tokenized word-level array blocks matched with absolute start and end timing fields.
    * *Text Structure:* The matching literary script delivered as clean, unformatted UTF-8 text.

### Technical Documentation
* **Functionality:** This program allows users to re-run the alignment matching engine using an existing, saved WhisperX transcription file (`*_ai_raw.json`) instead of transcribing the audio file again. It reconstructs the subtitle assets and time mappings directly from the cached data.
* **Operation:** 
    1. Run the script. A file selection window will open.
    2. Select the `*_ai_raw.json` file.
    3. The program searches for the corresponding `.txt` file in the same folder, recalculates the phonetic alignment matrices, and updates the `.ass` output file.
* **Logic:** 
    * **Cache Processing:** It parses the WhisperX JSON structures directly to access the character/word segment lists.
    * **Timeline Reconstruction:** It rebuilds the character-to-time map (`ki_timeline`) by taking each segment's start and end times and distributing the duration linearly across the characters in that segment.
    * **Re-Mapping:** It maps the clean text file against this timeline using the matching thresholds, completely avoiding resource-heavy AI model inferencing tasks.
* **Special Elements and Ideas:** 
    * **Offline Development Loop:** Decoupling the alignment logic from WhisperX's execution model means users do not need access to a GPU or neural network execution runtime environment once the raw JSON is generated. This allows fast tuning of thresholds (`MATCH_THRESHOLD`) or tweaking of text formatting parameters instantly.

---

## 5. manualaligncorrectionplusfeedback.py

### Input / Output Perspective
* **Execution Environment:** Behaves identically to `manualaligncorrection.py`. Driven by standalone GUI selection frameworks, making its physical execution path irrelevant.
* **Input Files & Location:** Requires the selection of a `*_ai_raw.json` path via interactive window prompts. It automatically targets the matching `{basename}.txt` text file located in that exact directory.
* **Output Files & Location:** Re-compiles or updates both the `{basename}.ass` script and the timestamped text tracking matrices directly in the source directory.
* **Concrete Input Format:** Identical dataset specifications to `manualaligncorrection.py`. The fundamental difference lies in the integration of real-time trace routines and extended standard out log reporting streams, rather than altering file schemas.

### Technical Documentation
* **Functionality:** An upgraded, highly verbose version of `manualaligncorrection.py`. While it shares the same core I/O pipeline and architecture, it features enhanced terminal diagnostic tracking and tighter condition checks to debug alignment failures on complex scripts.
* **Operation:** 
    1. Launch the script and select your target `*_ai_raw.json` file via the file explorer window.
    2. The terminal displays real-time diagnostic printouts tracking text segment indices, matching scores, window search margins, and fallback step logs.
    3. Outputs the compiled `.ass` structure in the same directory.
* **Logic:** 
    * Similar to the basic manual alignment script, but it wraps execution checkpoints with detailed diagnostic tracing logic.
    * It exposes search indexes explicitly (`f_search_start`, `f_search_end`) and prints detailed warnings when fallback strategies like `DELETION_STRETCH` stretch an unmatched text sequence across unmapped audio frames.
* **Special Elements and Ideas:** 
    * **Algorithmic Transparency:** This script is designed specifically for debugging edge cases where scripts contain heavy narrative descriptions that are not spoken aloud in the audio tracking file. The detailed log structures let you observe exactly where the text pointer loses track of the audio timeline, simplifying the calibration of the `MATCH_THRESHOLD` parameter.
