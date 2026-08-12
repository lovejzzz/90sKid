# V68 Cineon DPX exchange and profile-isolation audit

Date: 2026-08-11
Status: delivery-contract implementation; V66 image model unchanged

## Conclusion

V68 implements the separation identified by V67. The engine can now deliver
the same formed 5279 negative as unsigned 10-bit RGB printing-density DPX data,
before the provisional Cineon display curve and before the Blu-ray finish.

This is not a new look. The decoded 12-bit projection and scan masters are
bit-for-bit identical to V66. V68 changes the exchange boundary and fixes a
cross-profile reproducibility fault discovered by the expanded tests.

## The corrected mental model

Four stages must not be conflated:

1. **5279 image formation** — exposure, speed layers, finite sites, dye/coupler
   density, DIR transport and negative MTF;
2. **scanner data coordinate** — spectral primary correction, D-min reference,
   Spirit aperture and 10-bit printing-density code;
3. **viewing transform** — a named way to turn negative density data into
   display light;
4. **finish** — a best-light, DI or Blu-ray contrast/colour decision.

Our current 5279 claim belongs mainly to stage 1. V66 corrects stage 2 to a
coherent printing-density coordinate. The current open scan map and Blu-ray
finish remain useful witnesses at stages 3 and 4, but neither is part of the
intrinsic film stock.

This explains an important perceptual ambiguity in earlier versions: a scan
could look too green, too contrasty or too “digital” even when the stochastic
negative stage was unchanged, because the judged image also included an
unmeasured viewing policy.

## DPX contract

The new optional `--cineon-dpx` delivery writes:

- SMPTE ST 268-1 DPX v2.0;
- descriptor `50`: RGB;
- transfer characteristic `1`: printing density;
- colorimetric specification `1`: printing density;
- unsigned 10-bit samples, filled 32-bit packing;
- reference low code/density `0 / 0.00`;
- reference high code/density `1023 / 2.048`;
- Kodak reference-black aim retained at code `95`.

The data are generated inside the shared dual-observer traversal from the same
formed negative and the same Spirit-apertured scanner density that feed the
scan view. No second stochastic negative is formed. No Rec.709 matrix, display
gamma or Blu-ray finish enters the DPX path.

Primary sources:

- [SMPTE ST 268-1:2014 DPX](https://pub.smpte.org/latest/st268-1/st0268-1-2014_stable2015.pdf)
- [Kodak Cineon File Format Description](https://www.kodak.com/content/products-brochures/Film/Cineon-File-Format-Description.pdf)
- [Kodak H-387 Digital LAD and Cineon calibration aims](https://www.kodak.com/content/products-brochures/Film/Users-Guide-and-Digital-Recorder-Calibration-and-Aims-H-387.pdf)

SMPTE explicitly says DPX does not define input, output or display-device
characteristics. A printing-density DPX is therefore exchange data, not a
picture that QuickTime should be expected to show correctly without a named
view transform.

## Native 5.7K validation

Source: T020 frame 0, `5760×4320`, V66 physical profile.

### Display masters did not change

| Branch | V66 decoded MD5 | V68 decoded MD5 |
| --- | --- | --- |
| 2383 projection | `d77e31f7cf9c207273da2f34949047ef` | `d77e31f7cf9c207273da2f34949047ef` |
| scan/Blu-ray witness | `d43af174bd6859ff5be73b7a1ad34de8` | `d43af174bd6859ff5be73b7a1ad34de8` |

### DPX validation

- size: `99,534,464` bytes;
- FFmpeg-decoded samples equal direct 32-bit-word unpacking: **true**;
- decoded planar payload MD5: `ceb2bb0d15251e87740528c1d59c08fe`;
- RGB code minima: `[52, 11, 0]`;
- RGB medians: `[290, 285, 212]`;
- RGB maxima: `[715, 723, 781]`;
- code-1023 fraction: zero in all records.

The asymmetric fraction at or below code 95 (`0.35% / 1.25% / 11.92%`) is not
display clipping. It is legal sub-reference negative-density data and is one
reason a generic image viewer is the wrong diagnostic instrument for this
file.

Image computation remained `30.54 s/frame`; complete ProRes, review, audio and
DPX finalization took `41.56 s` wall time. The DPX route adds no second film or
scanner evaluation.

## Profile-state fault found and fixed

The new regression order exposed a pre-existing downgrade failure:

- apply V66;
- then request V44/V45 in the same interpreter;
- the V59+ clear-print spectral D-min and derived scanner neutral anchors could
  remain active even though the profile claimed archive coordinates.

Consequently V45's official-CIE delta changed from its checksum-locked
`0.00456916755` RMS to `0.00390320027` RMS. A fresh process still passed, which
made this specifically a process-history fault.

The fix restores the archive 2383 spectral D-min before historical profile
cache construction, removes later diagnostic state, and refreshes scanner
anchors only after the final archive Status-M tables are installed. The
V66→V44 downgrade now matches a clean interpreter array-for-array, and the V45
audit again passes.

This matters beyond testing: a versioned research engine is not reproducible if
its pixels depend on which profile happened to run first.

## Reproducibility

- Engine output: `outputs/native_5k_v68_cineon_dpx_contract_1f/T020/`
- Audit script: `src/audit_v68_cineon_dpx_delivery.py`
- Audit JSON: `research_runs/v68_cineon_dpx_delivery_audit.json`
- DPX writer: `emulsion5279/io.py::CineonDPXSequenceWriter`
- DPX frame: `cineon_printing_density/00000000.dpx`

The next research boundary is a named, explicit view-policy interface. It must
consume this DPX coordinate and declare every display assumption; it must not
silently become another claim about 5279.
