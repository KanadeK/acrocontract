# Compatibility rule catalog

Rule IDs are stable within the `acrocontract.diff.v1` report schema.

| ID | Severity | Trigger |
|---|---|---|
| `ACR001` | info | Optional field added |
| `ACR002` | info | Alternate name/tooltip added |
| `ACR101` | warning | Mutual, unambiguous likely rename above the confidence threshold |
| `ACR102` | warning | Widget count/page changes or its center moves more than 12 PDF points |
| `ACR103` | warning | Alternate name/tooltip removed |
| `ACR104` | warning | Candidate newly requires viewer-generated appearances |
| `ACR201` | breaking | Field removed |
| `ACR202` | breaking | Field type changed |
| `ACR203` | breaking | Existing field became required |
| `ACR204` | breaking | Existing field became read-only |
| `ACR205` | breaking | Maximum length became finite or shrank |
| `ACR206` | breaking | Choice export value removed |
| `ACR207` | breaking | Duplicate fully-qualified name introduced |
| `ACR208` | breaking | AcroForm contract replaced by XFA-only content |
| `ACR209` | breaking | New required field added |

`ACR101` never changes values or a PDF. It records name, alternate-name, and first-widget position
component scores. A mapping becomes executable only after it appears in a plan whose reviewer has
deliberately set `reviewed` to `true`.
