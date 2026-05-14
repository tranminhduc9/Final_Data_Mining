package service

import (
	"regexp"
	"strings"
	"unicode"

	"golang.org/x/text/runes"
	"golang.org/x/text/transform"
	"golang.org/x/text/unicode/norm"
)

var (
	rePunct  = regexp.MustCompile(`[^a-z0-9\s]`)
	reSpaces = regexp.MustCompile(`\s+`)
)

func stripDiacritics(s string) string {
	t := transform.Chain(norm.NFD, runes.Remove(runes.In(unicode.Mn)), norm.NFC)
	result, _, _ := transform.String(t, s)
	return result
}

// normalizeLocation lowercases, strips diacritics, removes punctuation, collapses spaces.
func normalizeLocation(s string) string {
	s = strings.ToLower(s)
	s = stripDiacritics(s)
	s = rePunct.ReplaceAllString(s, "")
	s = reSpaces.ReplaceAllString(s, " ")
	return strings.TrimSpace(s)
}

// locationGroups maps normalized aliases to the list of search terms sent to Cypher.
// Terms include both diacritic and non-diacritic forms to cover all DB variants.
var locationGroups = []struct {
	keys  []string // what user might type (after normalizeLocation)
	terms []string // what we pass to Cypher CONTAINS (toLower applied in query)
}{
	{
		keys:  []string{"ha noi", "hanoi", "hn"},
		terms: []string{"hà nội", "ha noi", "hanoi"},
	},
	{
		keys:  []string{"ho chi minh", "hcm", "tphcm", "tp hcm", "sai gon", "saigon"},
		terms: []string{"hồ chí minh", "ho chi minh", "tphcm", "tp hcm", "hcm"},
	},
	{
		keys:  []string{"da nang", "danang", "dn"},
		terms: []string{"đà nẵng", "da nang", "danang"},
	},
	{
		keys:  []string{"hai phong", "haiphong", "hp"},
		terms: []string{"hải phòng", "hai phong", "haiphong"},
	},
	{
		keys:  []string{"can tho", "cantho"},
		terms: []string{"cần thơ", "can tho", "cantho"},
	},
	{
		keys:  []string{"bien hoa", "bienhoa"},
		terms: []string{"biên hòa", "bien hoa", "bienhoa"},
	},
	{
		keys:  []string{"vung tau", "vungtau"},
		terms: []string{"vũng tàu", "vung tau", "vungtau"},
	},
}

// ExpandLocationSearchTerms converts a raw location string from the user into
// a list of search terms for Cypher CONTAINS. Handles abbreviations, diacritics,
// punctuation, and spacing variants (e.g. "TP.  HCM", "tphcm", "Hồ Chí Minh").
// Falls back to the normalized input when no known alias group matches.
func ExpandLocationSearchTerms(raw string) []string {
	normalized := normalizeLocation(raw)
	for _, group := range locationGroups {
		for _, key := range group.keys {
			if strings.Contains(normalized, key) || strings.Contains(key, normalized) {
				return group.terms
			}
		}
	}
	return []string{normalized}
}
