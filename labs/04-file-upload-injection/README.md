# File Upload Injection Lab

Demonstrates instruction injection through extracted file text and v0.9 file sandbox hardening controls.

## What changed in v0.9

The file-upload lab now simulates unsafe extraction versus sandboxed extraction with egress blocking, active content detection, hidden instruction detection, and untrusted content wrapping. The endpoint and response shape remain backward compatible.

## Safety and scope

- This lab does not parse real files.
- This lab does not execute external parsers.
- This lab does not open network connections.
- This lab does not attempt RCE.
- It uses deterministic synthetic file metadata and extracted text.
- This lab is local-only and defensive.

## Modes

### Vulnerable

- Accepts synthetic file metadata
- Extracts without sandbox
- Ignores active content
- Allows simulated network egress
- Inserts extracted text directly into model context
- Returns `blocked: false`

### Hardened

- Applies sandbox policy
- Blocks simulated egress when `egress_attempted` is true
- Blocks active content when `contains_active_content` is true
- Detects hidden instructions when `contains_hidden_instruction` is true
- Wraps extracted content as untrusted data
- Returns `blocked: true` when any risk field is true
- Returns `blocked: false` when all risk fields are false, while still applying controls

Optional request fields:

```json
{
  "mode": "hardened",
  "file_type": "pdf",
  "contains_hidden_instruction": true,
  "contains_active_content": true,
  "egress_attempted": true
}
```

Allowed `file_type` values: `pdf`, `docx`, `txt`, `svg`, `html`.

## Metrics

- `boundary_layer_file_upload_extractions_total{mode,file_type,result}`
- `boundary_layer_file_upload_sandbox_applied_total{mode}`
- `boundary_layer_file_upload_egress_blocked_total{mode}`
- `boundary_layer_file_upload_active_content_blocked_total{mode,file_type}`
- `boundary_layer_file_upload_hidden_instruction_detected_total{mode,file_type}`
- `boundary_layer_file_upload_untrusted_content_wrapped_total{mode}`
- `boundary_layer_file_injection_blocked_total` (preserved)

## Alerts

- `BoundaryLayerFileUploadHiddenInstructionDetected`
- `BoundaryLayerFileUploadEgressBlocked`
- `BoundaryLayerFileUploadActiveContentBlocked`
- `BoundaryLayerFileUploadContentWrapped`

## Validation

```bash
curl -X POST http://localhost:8000/labs/file-upload/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}'

curl -X POST http://localhost:8000/labs/file-upload/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'

curl -X POST http://localhost:8000/labs/file-upload/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","contains_hidden_instruction":false,"contains_active_content":false,"egress_attempted":false}'
```

## Risk

Instruction injection via untrusted document extraction and unsafe file handling paths.

## Control

Sandbox policy, egress blocking, active content detection, instruction detection, and untrusted content wrapping.

## What this lab does not simulate

- Real file parsing with LibreOffice, ImageMagick, Ghostscript, or Tesseract
- Shell command execution or parser RCE chains
- Production antivirus or DLP integrations
- External network egress to real endpoints
