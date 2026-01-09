// Test script to verify key signature mapping for all 14 supported keys
// Run this in browser console or Node.js to verify mappings

// Map music21 key names to VexFlow key signatures
function getKeySignature(keyName) {
    const signatures = {
        'C': 'C',      // C major: 0 sharps/flats
        'G': 'G',      // G major: 1 sharp
        'D': 'D',      // D major: 2 sharps
        'A': 'A',      // A major: 3 sharps
        'F': 'F',      // F major: 1 flat
        'Bb': 'Bb',    // Bb major: 2 flats
        'B-': 'Bb',    // Alternative notation from music21
        'Eb': 'Eb',    // Eb major: 3 flats
        'E-': 'Eb',    // Alternative notation from music21
        'a': 'Am',     // A minor: 0 sharps/flats
        'e': 'Em',     // E minor: 1 sharp
        'b': 'Bm',     // B minor: 2 sharps
        'd': 'Dm',     // D minor: 1 flat
        'g': 'Gm',     // G minor: 2 flats
        'c': 'Cm',     // C minor: 3 flats
        'f#': 'F#m',   // F# minor: 3 sharps
        'f♯': 'F#m'    // Alternative notation
    };
    return signatures[keyName] || 'C';
}

// Test with keys as extracted from music21
const testKeys = [
    { music21: 'C', expected: 'C', accidentals: '0' },
    { music21: 'G', expected: 'G', accidentals: '1♯' },
    { music21: 'D', expected: 'D', accidentals: '2♯' },
    { music21: 'A', expected: 'A', accidentals: '3♯' },
    { music21: 'F', expected: 'F', accidentals: '1♭' },
    { music21: 'B-', expected: 'Bb', accidentals: '2♭' },
    { music21: 'E-', expected: 'Eb', accidentals: '3♭' },
    { music21: 'a', expected: 'Am', accidentals: '0' },
    { music21: 'e', expected: 'Em', accidentals: '1♯' },
    { music21: 'b', expected: 'Bm', accidentals: '2♯' },
    { music21: 'd', expected: 'Dm', accidentals: '1♭' },
    { music21: 'g', expected: 'Gm', accidentals: '2♭' },
    { music21: 'f#', expected: 'F#m', accidentals: '3♯' },
    { music21: 'c', expected: 'Cm', accidentals: '3♭' }
];

console.log('Key Signature Mapping Test');
console.log('='.repeat(70));
console.log('music21 key | VexFlow key | Expected | Accidentals | Status');
console.log('='.repeat(70));

let allPassed = true;

testKeys.forEach(test => {
    const result = getKeySignature(test.music21);
    const passed = result === test.expected;
    const status = passed ? '✓ PASS' : '✗ FAIL';

    if (!passed) allPassed = false;

    console.log(
        `${test.music21.padEnd(11)} | ${result.padEnd(11)} | ${test.expected.padEnd(8)} | ${test.accidentals.padEnd(11)} | ${status}`
    );
});

console.log('='.repeat(70));
console.log(allPassed ? '✓ All tests passed!' : '✗ Some tests failed!');
console.log('='.repeat(70));

// Export for Node.js if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { getKeySignature, testKeys };
}
