# Key Signature Display Implementation

**Issue**: g8aural-z9i - Phase 5: Notation enhancements for key signatures

**Date**: 2026-01-08

## Overview

Implemented key signature display in the VexFlow notation rendering to correctly show key signatures for all 14 supported keys (7 major, 7 minor) with up to 3 sharps or flats.

## Implementation Details

### 1. Backend Changes (app.py)

#### Added Reactive Value
```python
current_key = reactive.Value(None)  # Store the key of the current progression
```

#### Key Extraction from Progression
```python
# Extract the key from the first chord in the progression
# RomanNumeral objects have a key attribute (music21.key.Key object)
progression_key = str(progression[0].key).split()[0] if progression else 'C'
current_key.set(progression_key)
```

**Note**: music21 returns keys with '-' for flats (e.g., 'B-', 'E-') instead of 'b' notation.

#### Updated renderNotation Messages
Added `"key": current_key()` parameter to both `renderNotation` message calls:
1. Line 341-347: When correct answer is provided
2. Line 427-433: When hint button is clicked

### 2. Frontend Changes (www/notation.js)

#### Added getKeySignature() Function
Maps music21 key names to VexFlow key signature format:

```javascript
function getKeySignature(keyName) {
    const signatures = {
        // Major keys
        'C': 'C',      // 0 sharps/flats
        'G': 'G',      // 1 sharp
        'D': 'D',      // 2 sharps
        'A': 'A',      // 3 sharps
        'F': 'F',      // 1 flat
        'Bb': 'Bb',    // 2 flats
        'B-': 'Bb',    // Alternative notation from music21
        'Eb': 'Eb',    // 3 flats
        'E-': 'Eb',    // Alternative notation from music21

        // Minor keys
        'a': 'Am',     // 0 sharps/flats
        'e': 'Em',     // 1 sharp
        'b': 'Bm',     // 2 sharps
        'd': 'Dm',     // 1 flat
        'g': 'Gm',     // 2 flats
        'c': 'Cm',     // 3 flats
        'f#': 'F#m',   // 3 sharps
        'f♯': 'F#m'    // Alternative notation
    };
    return signatures[keyName] || 'C';
}
```

#### Updated renderNotation() Function
1. Added `key` parameter to function signature
2. Added key signature to stave after clef:

```javascript
// Create stave with key signature
const stave = new VF.Stave(10, 40, 680);
stave.addClef("treble");

// Add key signature if key is provided
if (key) {
    const vexflowKey = getKeySignature(key);
    stave.addKeySignature(vexflowKey);
}

stave.setContext(context).draw();
```

#### Updated Message Handler
```javascript
Shiny.addCustomMessageHandler("renderNotation", function(message) {
    renderNotation(message.progression, message.noteNames,
                   message.chordSymbols, message.cadenceType, message.key);
});
```

## Key Mappings

### Major Keys (7 keys)
| music21 Key | VexFlow Key | Accidentals |
|-------------|-------------|-------------|
| C           | C           | None        |
| G           | G           | 1♯ (F♯)     |
| D           | D           | 2♯ (F♯, C♯) |
| A           | A           | 3♯ (F♯, C♯, G♯) |
| F           | F           | 1♭ (B♭)     |
| B- (or Bb)  | Bb          | 2♭ (B♭, E♭) |
| E- (or Eb)  | Eb          | 3♭ (B♭, E♭, A♭) |

### Minor Keys (7 keys)
| music21 Key | VexFlow Key | Accidentals |
|-------------|-------------|-------------|
| a           | Am          | None        |
| e           | Em          | 1♯ (F♯)     |
| b           | Bm          | 2♯ (F♯, C♯) |
| d           | Dm          | 1♭ (B♭)     |
| g           | Gm          | 2♭ (B♭, E♭) |
| f# (or f♯)  | F#m         | 3♯ (F♯, C♯, G♯) |
| c           | Cm          | 3♭ (B♭, E♭, A♭) |

## Testing

### Key Extraction Test
Verified that key extraction works correctly for all 14 keys:
```bash
source .venv/bin/activate
python test script
```

Results confirm:
- All keys are extracted correctly from music21 RomanNumeral objects
- Flat keys use '-' notation (B-, E-) in music21 format
- Both notations are handled in getKeySignature() mapping

### Test Files
- `test_key_signatures.js`: JavaScript test for key signature mapping verification

## Files Modified

1. `/home/andrie/wsl-github/g8aural/app.py`
   - Line 145: Added `current_key` reactive value
   - Line 223-225: Extract key from progression
   - Line 232: Store key in reactive value
   - Line 346: Pass key to renderNotation (correct answer)
   - Line 432: Pass key to renderNotation (hint)

2. `/home/andrie/wsl-github/g8aural/www/notation.js`
   - Line 32-57: Added `getKeySignature()` function
   - Line 60: Updated function signature to accept key parameter
   - Line 66-75: Added key signature to stave
   - Line 249: Updated message handler to pass key parameter

## Edge Cases Handled

1. **music21 flat notation**: Both 'Bb'/'Eb' and 'B-'/'E-' formats are supported
2. **F# minor Unicode**: Both 'f#' and 'f♯' formats are supported
3. **Missing key**: Defaults to 'C' major if key not found
4. **Null/undefined key**: Gracefully handles missing key parameter

## Verification Steps

To verify the implementation:
1. Start the app: `shiny run app.py --port 8080`
2. Play a cadence and view notation
3. Check that key signature displays before the first chord
4. Test with different keys (can be verified by chord symbols)
5. Special attention to F# minor (should show 3 sharps: F♯, C♯, G♯)

## Dependencies

- VexFlow 4.2.2 (already included via CDN)
- music21 (already installed for chord generation)

## Status

✓ Implementation complete
✓ All 14 keys supported
✓ Key extraction working correctly
✓ VexFlow key signature display integrated
⏳ Awaiting user verification before closing issue

## Next Steps

1. User testing and verification
2. Visual confirmation of all key signatures
3. Close issue after user approval
4. Proceed to Phase 6: Comprehensive testing (g8aural-yp9)
