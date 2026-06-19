# Scryfall API Reference

Base URL: `https://api.scryfall.com`  
Protocol: HTTPS only (TLS 1.2+), UTF-8 responses.

## Required Headers

Every request must include:
- `User-Agent: <AppName>/<Version>` — set explicitly; do not let the HTTP library choose
- `Accept: */*` or `Accept: application/json`

## Rate Limits — HARD LIMITS, DO NOT EXCEED

| Endpoint | Limit |
|---|---|
| `/cards/search` | 2/second (wait 500ms between calls) |
| `/cards/named` | 2/second (wait 500ms between calls) |
| `/cards/random` | 2/second (wait 500ms between calls) |
| `/cards/collection` | 2/second (wait 500ms between calls) |
| All other endpoints | 10/second (wait 100ms between calls) |
| `*.scryfall.io` (image CDN) | No rate limit |

**Consequences of exceeding limits:**
- HTTP 429 Too Many Requests → access throttled for 30 seconds
- Repeated violations → **temporary or permanent application ban**
- Ignoring 429 responses is not acceptable

**Always prefer bulk data over repeated API calls** when looking up many cards, names, or images.  
Cache all API responses for at least 24 hours.

## Bulk Data (Preferred for Large Lookups)

Bulk data is regenerated every 12 hours. Fetch the file list first to get current download URLs (URLs change daily):

```
GET https://api.scryfall.com/bulk-data
```

| File | Size | Description |
|---|---|---|
| Oracle Cards | ~168 MB | One object per Oracle ID (canonical card version) |
| Unique Artwork | ~247 MB | One object per unique illustration |
| Default Cards | ~522 MB | Every English card object |
| All Cards | ~2.35 GB | Every card in every language |
| Rulings | ~24 MB | All rulings, keyed by `oracle_id` |

Download URLs are on `*.scryfall.io` (no rate limit).  
Price data in bulk files is stale after 24 hours. Gameplay data (names, Oracle text, costs) changes much less frequently — weekly refresh is usually sufficient.

## Card Endpoints

| Method | Endpoint | Rate | Description |
|---|---|---|---|
| GET | `/cards/search?q=<query>` | 2/s | Full-text search; paginated 175/page |
| GET | `/cards/named?exact=<name>` | 2/s | Exact card name lookup |
| GET | `/cards/named?fuzzy=<name>` | 2/s | Fuzzy card name lookup |
| GET | `/cards/autocomplete?q=<str>` | 10/s | Name autocomplete (up to 20 results) |
| GET | `/cards/random` | 2/s | Random card |
| POST | `/cards/collection` | 2/s | Batch lookup by identifiers (up to 75) |
| GET | `/cards/:id` | 10/s | Card by Scryfall UUID |
| GET | `/cards/:code/:number(/:lang)` | 10/s | Card by set code + collector number |
| GET | `/cards/multiverse/:id` | 10/s | Card by Gatherer multiverse ID |
| GET | `/cards/mtgo/:id` | 10/s | Card by MTGO catalog ID |
| GET | `/cards/arena/:id` | 10/s | Card by Arena ID |
| GET | `/cards/tcgplayer/:id` | 10/s | Card by TCGplayer product ID |
| GET | `/cards/cardmarket/:id` | 10/s | Card by Cardmarket product ID |

### /cards/search Parameters

| Param | Type | Default | Description |
|---|---|---|---|
| `q` | String | required | Fulltext search query (max 1000 chars) |
| `unique` | String | `cards` | Rollup mode: `cards`, `art`, `prints` |
| `order` | String | `name` | Sort: `name`, `set`, `released`, `rarity`, `color`, `cmc`, `power`, `toughness`, `edhrec`, `usd`, `tix`, `eur`, `artist`, `review` |
| `dir` | String | `auto` | Direction: `auto`, `asc`, `desc` |
| `include_extras` | Boolean | false | Include tokens, planes, etc. |
| `include_multilingual` | Boolean | false | Include all language printings |
| `include_variations` | Boolean | false | Include rare variants |
| `page` | Integer | 1 | Page number |
| `format` | String | `json` | `json` or `csv` |

## Catalog Endpoints (10/s)

All return `{ object: "catalog", total_values: N, data: [strings...] }`.

| Endpoint | Description |
|---|---|
| `/catalog/card-names` | All Oracle card names |
| `/catalog/creature-types` | All creature subtypes |
| `/catalog/card-types` | All card types |
| `/catalog/supertypes` | All supertypes |
| `/catalog/artifact-types` | All artifact subtypes |
| `/catalog/enchantment-types` | All enchantment subtypes |
| `/catalog/land-types` | All land subtypes |
| `/catalog/planeswalker-types` | All planeswalker subtypes |
| `/catalog/spell-types` | All instant/sorcery subtypes |
| `/catalog/keyword-abilities` | All keyword abilities |
| `/catalog/keyword-actions` | All keyword actions |
| `/catalog/ability-words` | All ability words |
| `/catalog/powers` | All power values |
| `/catalog/toughnesses` | All toughness values |
| `/catalog/loyalties` | All loyalty values |
| `/catalog/watermarks` | All watermarks |

## Sets Endpoints (10/s)

| Endpoint | Description |
|---|---|
| `GET /sets` | All sets |
| `GET /sets/:code` | Set by three-letter code |
| `GET /sets/:id` | Set by Scryfall UUID |

## Other Endpoints

| Endpoint | Description |
|---|---|
| `GET /rulings/:id` | Rulings for a card by Scryfall UUID |
| `GET /symbology` | All card symbols |
| `GET /symbology/parse-mana?cost=<str>` | Parse a mana cost string |

## Scryfall Card Object

### Core Fields (always present)

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Scryfall unique ID for this printing |
| `oracle_id` | UUID | Consistent across reprints (absent on `reversible_card`) |
| `name` | String | Card name; faces joined by ` // ` |
| `lang` | String | Language code |
| `layout` | String | `normal`, `transform`, `split`, `flip`, `adventure`, `modal_dfc`, `reversible_card`, … |
| `object` | String | Always `"card"` |
| `uri` | URI | Link to this card on the API |
| `scryfall_uri` | URI | Link to card on Scryfall website |
| `prints_search_uri` | URI | All reprints of this card |
| `rulings_uri` | URI | Rulings for this card |

### Gameplay Fields

| Field | Type | Nullable | Description |
|---|---|---|---|
| `cmc` | Decimal | | Converted mana cost (mana value) |
| `color_identity` | Colors | | Commander color identity |
| `colors` | Colors | N | Card colors (null means colors are on `card_faces`) |
| `color_indicator` | Colors | N | Colors from color indicator dot |
| `mana_cost` | String | N | Cost string e.g. `{2}{G}{G}`; `""` if no cost |
| `type_line` | String | | Full type line |
| `oracle_text` | String | N | Oracle rules text |
| `power` | String | N | Power (may be `*`) |
| `toughness` | String | N | Toughness (may be `*`) |
| `loyalty` | String | N | Starting loyalty |
| `keywords` | Array | | Keyword abilities |
| `legalities` | Object | | Format → `legal`/`not_legal`/`restricted`/`banned` |
| `reserved` | Boolean | | On Reserved List |
| `produced_mana` | Colors | N | Mana colors this card can produce |
| `edhrec_rank` | Integer | N | EDHREC popularity rank |
| `all_parts` | Array | N | Related cards (tokens, meld parts, etc.) |
| `card_faces` | Array | N | Face objects for multiface cards |

### Print Fields (printing-specific)

| Field | Type | Description |
|---|---|---|
| `set` | String | Set code |
| `set_name` | String | Full set name |
| `collector_number` | String | Collector number (may contain letters or ★) |
| `rarity` | String | `common`, `uncommon`, `rare`, `mythic`, `special`, `bonus` |
| `artist` | String | Illustrator name |
| `image_uris` | Object | Image URLs by format (`small`, `normal`, `large`, `png`, `art_crop`, `border_crop`) |
| `prices` | Object | `usd`, `usd_foil`, `usd_etched`, `eur`, `eur_foil`, `tix` as strings |
| `finishes` | Array | `foil`, `nonfoil`, `etched` |
| `frame` | String | Frame year/style |
| `border_color` | String | `black`, `white`, `borderless`, `yellow`, `silver`, `gold` |
| `booster` | Boolean | Found in boosters |
| `digital` | Boolean | Video-game-only release |
| `reprint` | Boolean | Is a reprint |
| `promo` | Boolean | Promotional print |
| `released_at` | Date | First release date |

## Colors and Mana Symbology

Colors are represented as arrays of uppercase single-character strings:

| Code | Color | Example mana symbol |
|---|---|---|
| `W` | White | `{W}` |
| `U` | Blue | `{U}` |
| `B` | Black | `{B}` |
| `R` | Red | `{R}` |
| `G` | Green | `{G}` |
| `C` | Colorless | `{C}` |

Mana cost notation uses the Comprehensive Rules plaintext format: `{2}{G}{G}`, `{W/U}`, `{2/W}`, `{W/P}`, `{X}`, `{S}` (snow), `{T}` (tap), `{Q}` (untap).  
A null/missing color field means the information is not pertinent (not that the card is colorless).  
Color arrays are not guaranteed to be in any particular order.

## Error Objects

All errors return HTTP 4XX or 5XX with a JSON body:

```json
{
  "object": "error",
  "status": 404,
  "code": "not_found",
  "details": "The requested object or REST method was not found.",
  "type": "ambiguous",
  "warnings": ["..."]
}
```

| Field | Description |
|---|---|
| `status` | HTTP status code integer |
| `code` | Machine-readable error string |
| `details` | Human-readable explanation |
| `type` | Optional subtype (e.g., `ambiguous` for 404s) |
| `warnings` | Optional array of non-fatal warning strings |

## List Objects (Pagination)

Search results and collection listings return a List object:

```json
{
  "object": "list",
  "total_cards": 983,
  "has_more": true,
  "next_page": "https://api.scryfall.com/cards/search?...",
  "data": [...]
}
```

Always check `has_more` and follow `next_page` to retrieve all results. Each page contains up to 175 cards.

## Usage Policy

- Do not use Scryfall logos or imply Scryfall endorsement.
- Do not paywall access to Scryfall data.
- Do not repackage/republish Scryfall data without adding value.
- Do not use data to create new games or imply it is from another game.
- Card images: do not crop artist/copyright, distort, blur, or add watermarks.
