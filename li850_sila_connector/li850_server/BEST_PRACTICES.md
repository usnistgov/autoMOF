# Connector Development: Best Practices

DOs and DON'Ts for building a UniteLabs connector, grouped by area. Each rule has a short ID so
it can be referenced on its own (in a review comment, a docstring, another rule).

## How to add a new rule

- **ID format:** `<area>-<kebab-case-name>`, e.g. `name-suffix-by-role`. No sequential numbers;
  IDs must survive a rule being deleted later without shifting.
- **Area prefixes in use:** `name` (Naming), `doc` (Docstrings), `feat` (Features), `op`
  (Operations), `dt` (Data Types & Constraints), `io` (Input-Output), `err` (Error Handling),
  `proj` (Project Structure), `test` (Testing), `ver` (Versioning & Maintainability).
  Adding a new area means picking a new short prefix and listing it here.
- **A Don't-only rule's ID starts with `no-`.**
- **Format:**

  ```markdown
  - **`<id>`**: Do ... / Don't ...
    - **Why:** ... (only if the motivation isn't already obvious from the rule itself)
    - **Example:** ... (only when a concrete snippet or a "use X, not Y" contrast adds clarity)
  ```

  Not every rule needs a `Why:` or an `Example:`; add them only where they clarify something
  non-obvious. An `Example:` is a short code snippet or a direct before/after, never a bare file
  path.
- **Status tags** go right after the ID, in parentheses: `(open, ...)` for a question the team
  hasn't settled yet, `(needs verification, ...)` or `(proposed, ...)` for a rule sourced from
  docs or a proposal without confirmed real-code evidence. Remove the tag once it's resolved.

## Naming

### Connector project & repo naming

- **`name-title-case-display-name`**: Do write the display name in Title Case with spaces.
  This is the `connector_name` cookiecutter variable, and the GitLab project title.
  - **Example:** "Agilent Microplate Centrifuge".
- **`name-hyphen-case-project-name`**: Do use hyphen-case for the project name, auto-derived from
  the display name. This is the `project_name` cookiecutter variable, the repo path and top-level
  directory. Don't use underscores here.
  - **Example:** `agilent-microplate-centrifuge`.
- **`name-snake-case-package-name`**: Do use snake_case for the package name, auto-derived from the
  project name. This is the `package_name` cookiecutter variable, the internal import name. Don't
  use hyphens here.
  - **Example:** `agilent_microplate_centrifuge`, imported as `unitelabs.agilent_microplate_centrifuge`.
- **`name-no-unitelabs-in-project-name`**: Don't include `unitelabs` in the project or package name.
  The package is auto-namespaced to `unitelabs.<package_name>`, so repeating it is redundant.

### Display name format (proposed, pending team sign-off)

- **`name-brand-plus-model`**: Do name the display name `<Brand> <Model>`.
  - **Example:** "Hamilton Microlab STAR".
- **`name-series-suffix-for-hardware-family`**: Do append "Series" when one connector spans a
  hardware family rather than a single model.
  - **Example:** "Qinstruments Bioshake Series".
- **`name-platform-suffix-for-software`**: Do append "Platform" for a connector built around a
  software layer driving multiple devices.
  - **Example:** "Biotek Gen5 Platform".
- **`name-no-rename-without-migration-plan`**: Don't rename an existing connector's display name
  without a migration plan.
  - **Why:** it changes the derived package name too, which triggers a rebuild under a new import
    path that can be confused with the old one and break a customer's update path.
- **`name-hardware-family-naming`** (open, unresolved): no agreed convention yet for a connector
  covering multiple related devices sharing one protocol (e.g. Bioshake plus a TiltStation and a
  TurnStation): one shared family name, or separate connectors per device on a shared protocol layer.

### File & folder names

- **`name-folder-mirrors-class`**: Do name a feature's folder and module file in `snake_case`,
  matching the `PascalCase` class name.
  - **Example:** `random_number_provider/random_number_provider.py` for class
    `RandomNumberProvider`.
- **`name-short-file-names`**: Do keep every file name short. Don't repeat the connector/package
  name, including in the main protocol file.
  - **Example:** `errors.py`, `units.py`, `protocol.py`, not `file_system_errors.py` or
    `file_system_protocol.py`.

### Feature names

- **`name-suffix-by-role`**: Do name every feature class with a noun plus `Controller`, `Provider`,
  or `Service`, per the SiLA 2 standard: `Provider` for a feature with only information or sensor
  values (no controls), `Controller` for a feature that has any control capability (it can still
  expose properties), and `Service` for a feature
  not tied to hardware but to the SiLA server itself (e.g. meta SiLA features like the SiLAService).
  - **Why:** Accords with the [relevant SiLA best practices](https://docs.google.com/document/d/1nGGEwbx45ZpKeKYH18VnNysREbr1EXH6FqlCo03yASM/edit?tab=t.0#heading=h.cdjvmmq3hsbv)
  - **Example:** `TemperatureController: ...` (controls the device, and
    exposes readings too), `DeviceInformationProvider: ...` (readings only), `class
    ConnectionConfigurationService ...` (meta-feature, about the SiLA server).
- **`name-service-for-maintenance-features`**: Do use `Service` for a feature that isn't part of
  normal operation: teaching, calibration, and settings embedded in the device that configure how
  the server is used rather than actively driving the device.
  - **Why:** the qualifier is "not actively operating the device", which covers the SiLA server's
    own meta features and these maintenance ones alike.
  - **Example:** `TeachingService`, `CalibrationService`.
- **`name-actor-not-artifact`**: Do name a feature after the actor that does the work, not after
  the artifact it produces or consumes.
  - **Example:** `BarcodeReaderController`, not `BarcodeController`.
- **`name-no-feature-suffix`**: Don't include the word `Feature` in the class name.
  - **Why:** the base class already marks it as a feature; repeating that adds nothing.
  - **Example:** `TemperatureController`, not `TemperatureControllerFeature`.
- **`name-no-package-in-class-name`**: Don't repeat the connector/package name in the class name.
  - **Example:** `FileService`, not `FileSystemFileService`.
- **`name-no-abbreviations`**: Don't abbreviate. Spell out the full word.
  - **Example:** `LiquidLevelProvider`, not `LLProvider`.

### Operation and parameter names

- **`name-get-prefix`**: Do prefix unobservable properties with `get_`.
  - **Why:** the CDK strips it before deriving the public identifier, so it's purely a
    code-readability signal, not something a client ever sees.
  - **Example:** `get_serial_number`.
- **`name-subscribe-prefix`**: Do prefix observable properties with `subscribe_`.
  - **Why:** the CDK strips it before deriving the public identifier, so it's purely a
    code-readability signal that this property is a stream, not something a client ever sees.
  - **Example:** `subscribe_temperature`.
- **`name-verb-for-commands`**: Do start commands with an action verb, either standalone or followed
  by more context when needed. Complex commands use a verb-adjective-noun structure.
  - **Why:** unlike properties, the CDK doesn't strip any prefix from commands, so whatever verb
    you choose becomes part of the public identifier as-is.
  - **Example:** `read`, `write`, `delete`, `start_ramp`, `set_target`.
- **`name-full-words-for-identifiers`**: Do use full words in method names. Don't rely on
  abbreviations or acronyms.
  - **Example:** `get_server_uuid` derives the identifier `ServerUuid`, not `ServerUUID`.
- **`name-explicit-name-for-acronyms`**: Do set `name=` explicitly on the decorator when you need an
  acronym to stay uppercase in the public identifier.
  - **Why:** the automatic derivation only capitalizes the first letter of each word.
  - **Example:** `@sila.UnobservableCommand(name="Set ID Number")` on method `set_id_number` gives
    the identifier `SetIDNumber`; leaving `name=` unset gives `SetIdNumber` instead.
- **`name-no-redundant-context`**: Don't repeat the feature's own context in the operation name.
  - **Example:** on a `TemperatureController` feature, use `start_ramp` and `current`, not
    `start_temperature_ramp` and `current_temperature`.
- **`name-no-units-in-identifier`**: Don't include a unit in an identifier. Use a unit constraint
  instead and keep the name clean.
  - **Example:** `timeout`, not `timeout_ms`.

### Vendor terminology

- **`name-normalize-vendor-terminology`**: Do rename a vendor-specific term to the closest standard
  term when one applies. Don't expose the vendor's own word if a standard term already covers it.
  - **Why:** a client should never need to know that a specific vendor calls a door a "shutter".
  - **Example:** a vendor's "drawer", "flap", or "hatch" all become "door" in a UniteLabs connector.
- **`name-model-the-intent-not-the-mechanism`**: When a device combines two operations into one
  physical mechanism, do name it after the operation a client actually cares about, not the
  literal mechanical action.
  - **Why:** the mechanical action is a detail of that specific device; the intent is what the
    client actually cares about.
  - **Example:** model a mechanism that opens a door to present a plate as a `PlateCarrier` with
    `extend`/`retract`, not a `Door` with `open`/`close`, if presenting the plate is the real intent.
- **`name-standard-command-vocabulary`**: Do use a recognized standard verb when the device's
  operation matches one. When an operation is close to one of these but not exact, do use the
  standard name and document the difference in the docstring rather than coining a new variant.
  - **Why:** keeps the same operation recognizable by name across every UniteLabs connector.
  - **Example:** `initialize`, `deinitialize`, `reset`, `standby`, `start`, `stop`, `home`,
    `open`/`close`, `extend`/`retract`, `lock`/`unlock`, `seal`, `decap`/`recap`, `update`, `info`,
    `status`, `errors`.
- **`name-check-sila-base-feature-repo-first`**: Do check the SiLA base feature repository for an
  existing feature name before inventing a new one.
  - **Why:** reusing an established name keeps interoperability intact.

### Multi-instance naming

- **`name-parametrized-multi-instance`**: Do implement a repeated physical module as one
  parametrized class, registered once per instance. Don't write a separate class per instance.
  Also refer to `name-slot-id-for-homogeneous-instances` in case a shared feature matches the usage
  concern better.
  - **Why:** Allows for single concern features and separates clearly what part of the device is addressed.
  - **Example:** multiple pump channels, reader slots, bioreactor chambers.
- **`name-index-before-suffix`**: Do name each instance `<Noun><Index><Suffix>`, with the index
  injected via the `name=` field at construction time. Don't hardcode the index into the class
  definition or put it after the suffix.
  - **Example:** `Door1Controller`, not `DoorController1`, implemented as
    `super().__init__(..., name=f"Pipette {channel} Service", **kwargs)`.
- **`name-slot-id-for-homogeneous-instances`**: When the instances are interchangeable positions
  on one logical resource rather than independent modules, do expose a single generalized feature
  taking a slot identifier as a parameter, constrained to the valid range. Don't register one
  feature per position.
  - **Why:** As named in the example, if a setup feels "more hotel than door", exposing single features
    per "door", potentially makes the features dependent on each other and separates a single concern.
  - **Example:** `AccessCompartmentController.open(slot: int)` with a min/max constraint on
    `slot`, not `Door1Controller.open()` and `Door2Controller.open()` for a centrifuge with multiple slots.

### Consistency

- **`name-one-name-everywhere`**: Do pick one name and use it for the file, the class, and the
  public identifier. Don't let them diverge for the same feature.
  - **Why:** confuses anyone tracing a feature from the interface back to the code.

## Docstrings

### Format

- **`doc-google-style-docstrings`**: Do write docstrings in Google style. Don't use
  reStructuredText directives.
  - **Why:** the CDK's parser treats RST directives as deprecated and warns.
  - **Example:** avoid `.. parameter::`, `.. return::`.
- **`doc-no-types-in-docstring`**: Don't include type annotations inside a docstring's
  `Args:`/`Returns:` entries.
  - **Why:** the CDK warns and ignores them; types come only from the function signature.
  - **Example:** don't write `path (str): ...`; just write `path: ...`.
- **`doc-no-units-in-docstring`**: Don't state a unit in a docstring, neither in an
  `Args:`/`Returns:` entry nor in a property's one-line description. Do annotate it on the
  signature instead, as a `sila.constraints.Unit` on the parameter or return type.
  - **Why:** a unit written in prose is invisible to a client reading the interface, and it goes
    stale the moment the annotation changes. `Unit` is the one constraint that applies to return
    values as well as parameters, so there is always somewhere on the signature to put it. See
    `dt-unit-constants-in-io-units` for where the constants live.
  - **Example:** don't write `TargetSpeed: The target speed, in RPM.`, or `Parameter: the
    respective parameter. Units not included, always in 1/10 mm for the length dimension.`; write
    `TargetSpeed: The target speed.` and put the unit on the signature.
- **`doc-two-space-indent`**: Do indent entries under `Args:`/`Returns:`/`Raises:` by 2 spaces
  relative to the section header, not 4.
  - **Example:**

    ```python
    Args:
      Path: The absolute path of the folder to be scanned.
    ```

### Feature class docstrings

- **`doc-describe-what-and-when`**: Do open the class docstring with what the feature controls or
  provides, and the context in which it applies.
- **`doc-feature-docstring-scope`** (open, needs a team decision): a richer docstring style has
  been proposed, one that also documents call order requirements, pre-conditions, and
  cross-feature dependencies.

### Command docstrings

- **`doc-args-section-pascalcase`**: Do document each command parameter in an `Args:` section,
  with its name written in PascalCase, followed by a description.
  - **Example:**

    ```python
    Args:
      TargetSpeed: The target speed.
    ```

- **`doc-params-match-signature`**: Do document parameters in the same order as the function
  signature, one entry per parameter. Don't document a parameter that doesn't exist on the method.
  - **Why:** the CDK warns and drops any documented parameter it can't match to the signature.
- **`doc-returns-section-pascalcase`**: Do include a `Returns:` section for commands, with the
  name in PascalCase and a description of the returned value.
  - **Example:**

    ```python
    Returns:
      LimitCurveNames: List of limit curve names.
    ```

- **`doc-yields-section-pascalcase`**: Do document an `ObservableCommand`'s intermediate responses (the `intermediate:
  sila.Intermediate[T]` parameter) in a `Yields:` section, with the name in PascalCase and a
  description, the same way `Args:`/`Returns:` work.
  - **Example:**

    ```python
    Yields:
      Temperature: The current temperature.
    ```

### Property docstrings

- **`doc-no-args-on-properties`**: Don't include an `Args:` section on properties.
  - **Why:** a SiLA property never takes parameters.
- **`doc-no-returns-on-properties`**: Don't include a `Returns:` section on properties. Describe
  the return value directly in one line.
  - **Example:** `"""Whether the clamp is currently securing labware."""`

### Error docstrings

- **`doc-raises-to-override-description`**: Do add a `Raises:` entry, naming the same exception
  class, only when this specific operation needs different guidance than the exception's default
  description.
  - **Why:** the CDK merges both sources into one error set keyed by identifier, and the
    `Raises:` entry wins over the decorator's default for that one operation.
- **`doc-no-generic-error-documentation`**: Don't document errors that can happen on any operation.
  Do document only errors specific to that operation, the ones a caller has a reasonable way to
  react to. See Error Handling for which error categories belong in `Raises:`/`errors=` at all.
  - **Example:** don't document `ConnectionError` or `HardwareError` on every operation.

### No Example section

- **`doc-no-pythonic-examples`**: Don't include Python doctest-style examples in a docstring. Do
  explain a required call order or a state machine in plain text instead, if a method genuinely
  needs that context.
  - **Why:** the SiLA server is language-agnostic; a client may not be using Python at all.
  - **Example:** don't write `>>> await door_lock.lock(...)`.
- **`doc-sila-identifiers-in-descriptions`**: When a description has to refer to another operation,
  do name it by its SiLA identifier. Don't use a Python client's access syntax.
  - **Why:** we can't assume how the server is consumed. We follow the SiLA standards for compatibility.
  - **Example:** "Call the `DoorController.Lock` endpoint before the read `Read State` endpoint.",
    not "call `door_lock.lock()` first".

## Features

### Feature metadata

- **`feat-originator-reverse-domain`**: Do use reverse domain notation for `originator`.
  - **Example:** `io.unitelabs` for an internal UniteLabs connector, `<TLD>.<vendorname>` for a
    connector commissioned by an external vendor.
- **`feat-no-default-originator`**: Don't leave `originator` unset.
  - **Why:** it defaults to `org.silastandard`, which misrepresents the feature as an official
    SiLA standard feature instead of a UniteLabs one.
- **`feat-namespace-format-for-originator-category`**: Do write `originator` and `category` as
  lowercase letters and digits, dot-separated for hierarchy. Don't use uppercase letters, spaces,
  hyphens, or underscores.
  - **Why:** the SDK validates this format and raises an error otherwise.
  - **Example:** `filesystem`, `temperature`, `position.clamp.edgelock`.
- **`feat-category-domain-choice`**: Do pick a `category` that names one functional domain, and
  check existing connectors for a category that already fits before inventing a new one. Don't
  split a single domain into a deep dot hierarchy just for the sake of it; only nest when the
  feature genuinely belongs to a narrower sub-domain.
  - **Why:** keeps categories consistent and discoverable across connectors.
- **`feat-version-default-then-bump`**: Do leave `version` unset on a new feature. Do set it
  explicitly, as exactly `major.minor`, only once the feature's interface changes and the version
  needs to bump. Don't add a patch or label segment.
  - **Why:** the SDK already defaults `version` to `1.0` when left unset, and enforces exactly two
    numeric dot-separated parts whenever it's set explicitly.
  - **Example:** `1.0`, then `1.1`, not `1.0.1`.
- **`feat-maturity-level-draft-default`**: Do leave `maturity_level` unset on a UniteLabs
  connector's features. Don't set it to `Verified` or `Normative`.
  - **Why:** the SDK already defaults `maturity_level` to `Draft` when left unset; `Verified` and
    `Normative` are reserved for features that passed the formal SiLA community review process.

### Designing the interface

- **`feat-be-opinionated-about-interface-design`**: Do decide what to expose by asking what the user
  actually needs. Don't carry over an awkward device model just because that is how the vendor's
  manual describes it.
  - **Why:** a vendor's interface is shaped by their firmware and their history, and part of
    building a high-quality connector is questioning whether it serves the user.
    See also`name-normalize-vendor-terminology` and `name-model-the-intent-not-the-mechanism`.
  - **Example:** a Tecan Freedom EVO RoMA arm moves by registering waypoints and then traveling
    through them. As we prefere simple `move_by` and `move_to` interfaces, we abstract this waypoint registration.

### One feature per concern

- **`feat-one-feature-per-concern`**: Do give each feature a single domain or responsibility,
  independently understandable, even when two concerns share the same underlying resource. Don't
  bundle multiple concerns into one feature.
  - **Example:** separate `FolderService`, `FileService`, and `S3Service` features on one file
    system, not one combined feature.
  - **Example:** `get_position`, `move_to`, and `move_by` all serve the objective "controlling
    the position of a thing" and belong on the same feature.

### Feature registration

- **`feat-register-before-yield`**: Do register every feature with `app.register(...)` before
  `yield app` inside `create_app`.
  - **Why:** code placed after `yield app` only runs during teardown, once the server has already
    started serving, so a feature registered there never actually registers before a client connects.
  - **Example:**

    ```python
    app.register(MyFeature())
    yield app
    ```

    not

    ```python
    yield app
    app.register(MyFeature())  # too late, never registered before serving
    ```

## Endpoints: Properties & Commands

### Choosing Property vs Command

- **`op-observable-property-for-changing-values`**: Do use an `ObservableProperty` for a value
  where the client should be notified of changes. Do use an `UnobservableProperty` for a value
  that's static or read on demand.
  - **Example:** sensor readings and device status are Observable; serial number, firmware
    version, and configuration are Unobservable.
- **`op-no-side-effects-in-properties`**: Don't let a property change device state. If reading a
  value triggers a side effect on the device, model it as a command instead.
  - **Why:** properties are for reading, not acting.

### One value per endpoint

- **`op-property-per-value`**: Do expose each piece of information as its own property. Don't
  offer one endpoint that returns bundled information if that information is distinct.
  - **Why:** Getters should be defined around a single piece of data, otherwise the user has to find their
    value in a catalogue of values.
  - **Example:** `get_serial_number`, `get_instrument_name`, ... as individual Properties instead of a
    `get_device_information` endpoint.
- **`op-no-selector-parameter`**: Don't take a parameter whose only job is to select which piece
  of information to return. Do split it into one property per selectable value worth exposing.
  - **Why:** Similar to `op-property-per-value` but we also want to avoid a command that could simply
    be multiple properties. Also sometimes doesn't allow for proper annotation.
  - **Example:** `get_current_x_position`, `get_x_axis_speed` instead of
    `get_current_x_axis_parameter(parameter_selector: Literal['speed', 'position']) -> int`.
- **`op-no-redundant-properties`**: Don't expose "convenient" duplicates of getters, chose one, transforming them is on the user.
  - **Example:** Don't expose `get_state` + `get_state_numeric` + `get_state_string`

### Choosing Observable vs Unobservable Commands

- **`op-long-or-risky-commands-observable`**: Do make a command an `ObservableCommand` when it
  drives physical movement, or when it can run long enough (roughly upward of 300 ms) that a
  dropped connection during execution is a real risk.
  - **Why:** a client needs to be able to tell whether the command completed if the connection
    drops mid-call; an `UnobservableCommand` gives no way to know that.
- **`op-no-fake-progress`**: Don't add fabricated intermediate progress to an `ObservableCommand`
  when there's no real, calculable timing to report. Jump straight from 0 to 100 rather than
  inventing steps in between.
- **`op-indefinite-duration-start-stop-pair`**: Do model an action with no natural end point (it
  runs until explicitly told to stop) as an `UnobservableCommand` to start plus a separate
  `UnobservableCommand` to stop, not as one long-running `ObservableCommand`.
  - **Why:** an `ObservableCommand` is expected to be awaitable until done; an action that never
    completes on its own makes that a bad experience for the caller.
  - **Example:**

    ```python
    @sila.UnobservableCommand()
    async def start(self, target_speed: ..., acceleration_time: ...) -> None:
        """Start shaking at the given speed (no shaking duration is specified)."""

    @sila.UnobservableCommand()
    async def stop(self) -> None:
        """Stop shaking."""
    ```

- **`op-cancellable-movement-commands`**: Do support cancellation on every `ObservableCommand`
  that drives physical movement, so a client can abort it mid-operation.
  - **Why:** without it, a client is stuck waiting out a long physical motion it can no longer act on.

### Retries and idempotency

- **`op-prefer-idempotent-commands`**: Do design a command so that calling it twice has the same
  effect as calling it once, wherever the device allows it.
  This extends to endpoints that have wrap multiple device steps. Try to avoid an error partway through,
  that leaves the machine in a awkward state that is hard to recover from.
  - **Example:** calling `set_target(37)` a second time with the same value doesn't break
    anything; calling `open()` on a door that's already open should succeed as a no-op rather
    than raise.
- **`op-raise-on-already-in-progress`**: Where idempotency isn't possible, do raise a clear
  `ExecutionError` if the operation is already in progress. Don't silently no-op, and don't let an
  opaque hardware error surface instead.
  - **Example:** starting a run that's already running.
- **`op-caller-can-always-tell-outcome`**: Do make sure a caller can always tell whether a
  command succeeded or failed. A successful call should return normally; a failed call should raise an error.
  Idempotent commands return successfully, even if the device was already in the requested state.
  No differentiation is made between a command that was ignored because the device was already in the requested state
  and one that was run and changed the state to the requested state.
- **`op-recovery-through-normal-commands`**: Do make every state which is reachable through the normal
  command set, recoverable through the normal command set.
  - **Why:** A User should not need to use debugging or low-level feature to get out of a state an ordinary
    call put them in.

### Command parameters and return values

- **`op-no-boolean-success-response`**: Don't return a bare `bool` named `Success` to signal that
  a command worked. If the command returns normally, it succeeded; if something went wrong, it
  should raise an error instead.
- **`op-bool-param-over-split-methods`**: Where a setting has exactly two states and can never
  gain a third, do take a `bool` parameter on one endpoint. Don't split it into an enable and a
  disable endpoint. Where a third state is possible, use an enum from the start.
  This does not apply to actions that result in two states (e.g. door.open / door.closed is preferred over door.open(open:bool))
  - **Example:** `set_force_sensing(on: bool)`, not `enable_force_sensing()` plus
    `disable_force_sensing()`. Anything with a plausible third state gets an enum, see
    `dt-str-enum-for-status`.
- **`op-parameter-order-convention`**: Do order parameters by spatial axis first (`x`, `y`, `z`,
  kept adjacent), then by impact, highest first, and put a time or duration parameter last when
  there are only a few parameters.
  - **Example:** `seal(temperature, duration)`, not `seal(duration, temperature)`.

### Execution mode

- **`op-execution-mode-by-repeatability`**: Do restrict a command to a single execution at a
  time when it drives physical movement. Do allow queuing when only the end result matters and
  the command is idempotent.
  - **Why:** Two relative movement commands that would have been fine on their own, if queued, could crash the device. Dispensing twice might overflow a container. A good rule of thumb: if I run this twice, am I in the same state as running it only once?

### Statelessness

- **`op-expose-stateless-api`**: Endpoints of a connector should be stateless. If a device has
  internal states, abstract them away.
  - **Why:** States can be hard to track. When using an endpoint with the same parameters, the same thing should
    happen.
  - **Example:** instead of `set_temperature_target` followed by `start_incubation`, offer a
    single `start_incubation` that takes the target temperature as a parameter. But also more complex commands
    like an aspirate should be stateless by offering all parameters, including position and speeds, that effect
    the function of that endpoint.

- **`op-no-connect-command`**: Do not expose underlying communication control as a mandatory feature; only for debugging. Don't require a client to call a `connect()` command before
  issuing any other command. Do open the device connection during connector startup and close it
  during teardown instead.
  - **Why:** the connector manages its own state; the client shouldn't have to. This does not extend to initialization (see `io-no-movement-on-transport-open`)

### Conditional endpoints for device variants

- **`op-enabled-for-device-variants`**: Do use the decorator's `enabled=` callable to exclude an
  endpoint that doesn't apply to the connected device variant. It's evaluated once at startup, so
  if variant detection needs the device connected, make sure the connection opens before features
  are registered.
  - **Example:** `enabled=lambda self: self.protocol.is_device_variant(["TC"])`.

- **`op-enable-as-overload`**: Do use the decorator's `enable=` in combination with the `name=` parameter to
  expose the same endpoint with a different parameter set.
  - **Example:** A shaker comes in two version, one can set the shake direction, the other not:
    shake_device1(speed) & shake_device2(speed, direction), both decorated with `name="Shake"`, only one
    can be registered at a time.

## Data Types & Constraints

### Constraints

- **`dt-constraints-applied-to-all-values`**: Validation constraints (`MinimalInclusive`,
  `MaximalInclusive`, `Set`, `MinimalLength`) should be added to any values where they apply. Paramaters and
  return values are restricted based on actual device responses. Informational constraints, such as `Unit` and `ContentType`,
  add meaning for the client without applying any validations.
  - **Example:** `async def subscribe_current_temperature(self) -> sila.Stream[typing.Annotated[float, C, MinimalInclusive(0.0)]]: ...`
- **`dt-static-constraints-via-annotated`**: Do declare a parameter's valid range with
  `typing.Annotated[type, sila.constraints.X(...)]` when the constraint is known at
  code-authoring time and never changes.
  - **Example:** `typing.Annotated[pathlib.Path, sila.constraints.MinimalLength(1)]`.
- **`dt-runtime-constraints-on-startup`**: Do use `self.add_constraint(handler, parameter=...,
  constraints=[...])` inside `on_before_start` when the valid range depends on the connected
  device and can only be known once the connector queries it at startup.
  - **Example:**

    ```python
    async def on_before_start(self) -> None:
        max_value = await self.protocol.get_max_value()
        self.add_constraint(self.start, parameter="speed", constraints=[
            sila.constraints.MaximalInclusive(max_value),
        ])
    ```

- **`dt-validation-error-for-fully-dynamic-constraints`**: When a constraint can't be pinned down
  even at startup (it depends on state that can change per call), do document the valid range in
  the parameter description and register a validator for the endpoint.
  - **Why:** don't leave the caller without an explanation of why their input was rejected.
  - **Example:**

    ```python
    @sila.UnobservableCommand()
    async def method(self, speed: float) -> None:
        """
        Run the method at the given `Speed`.

        Args:
          Speed: The target speed. Must not exceed the current maximum speed.
        """
        ...
    @method.validator
    async def validate_speed(self, speed: float) -> None:
        max_value = await self.protocol.get_max_value()
        if speed > max_value:
            msg = f"Speed {speed} exceeds the current maximum of {max_value}."
            raise sila.ValidationError(msg, "speed")
    ```

### Binary data

- **`dt-binary-for-raw-data`**: Do use `bytes`, not `str`, for a raw byte payload (file contents,
  images, or any data without a fixed text encoding).
  - **Why:** a string has a maximum character limit of 2²¹ (~2MB) and carries an implicit encoding assumption that may not match the data.
- **`dt-content-type-for-known-binary-format`**: When the binary data has a known format, do tell
  the client what it is with a `ContentType` informational constraint.
  - **Example:** `"image/png"`, `"application/pdf"`.

### Structured, grouped data

- **`dt-dataclass-for-grouped-data`**: Do define a dataclass when a response bundles several
  related values, instead of a loose tuple or an unstructured string.
  - **Example:**

    ```python
    @dataclasses.dataclass
    class Metadata:
    """
    Metadata about a file.

    Attributes:
      Size: The size of the file in bytes.
      Owner: The username of the file's owner.
      CreatedAt: The timestamp when the file was created.
      LastModified: The timestamp when the file was last modified.
    """
        size: int
        owner: str
        created_at: datetime.datetime
        last_modified: datetime.datetime
    ```

- **`dt-no-raw-xml-json-string`**: Don't pass raw XML or JSON as a plain string. If the payload
  has structure, model that structure explicitly with a dataclass or as bytes annotated with
  `sila.constraints.ContentType` and, if there is a schema for the data, with `sila.constraints.Schema`.
- **`dt-no-nested-lists`**: Don't nest a `list` inside another `list` parameter or return value.
  - **Why:** SiLA's `List` type only holds basic types, structures, constrained types, or custom
    types, never another list.

### Enums and status values

- **`dt-enum-for-status`**: Do use an Enum for a status or state value, not a bare
  integer or string. Enums are converted into Constrained Strings in the SiLA interface,
  based on the Enum's member names.
  - **Why:** integers force clients to look up a table; strings carry their meaning with them.
  - **Example:**

    ```python
    class DeviceStatus(enum.Enum):
        IDLE = enum.auto()
        RUNNING = enum.auto()
        ERROR = enum.auto()
    ```

### Units

- **`dt-unit-constants-in-io-units`**: Do define unit constants once, in `io/units.py`, and import
  them wherever needed instead of redefining them per feature.
  - **Example:**

    ```python
    RPM = sila.constraints.Unit(
        label="RPM",
        components=[sila.constraints.UnitComponent(sila.constraints.SIUnit.SECOND, -1)],
        factor=1 / 60,
    )
    ```

- **`dt-propagate-device-native-units`**: Do propagate the unit the device actually uses. Don't
  silently convert it into something else because it seems more convenient.
  - **Why:** a silent conversion hides a transformation no client can see or verify, and creates a
    maintenance trap if it's ever wrong.
  - **Example:** if the device reports Kelvin, annotate the interface with Kelvin; don't subtract
    273.15 and expose Celsius instead.
- **`dt-fractional-unit-two-cases`**: If the device genuinely operates in a fractional unit (its
  own documentation defines its resolution that way), do expose it as-is and document the
  scaling, or define a custom unit label for it. If the device uses integers only as a firmware
  workaround for missing float support, do convert on the connector side and expose the standard
  unit instead. Whichever you choose, document it clearly.

### Coordinate systems

- **`dt-liquid-handler-origin-at-tip-bottom`**: On a liquid handler, do report and accept
  positions in a coordinate system whose origin is the bottom of the tip.
  - **Why:** this is conserved across every liquid handler we support, so a client moving
    between two of them doesn't have to re-derive the reference frame.

## Input-Output

### Initialization and teardown

- **`io-no-movement-on-transport-open`**: Whenever the connector starts and the transport is opened,
  not physical movement should happen on the device. This includes initialization and calibration.
  - **Why:** the user doesn't expect anything to happen from "just" starting the controlling software.
    Any actions in the open method would be called automatically by the connector if device connectivity is lost and regained.

## Error Handling

### The four SiLA error categories

- **`err-only-execution-errors-in-decorator-or-raises`**: Do declare only Execution errors in the
  decorator's `errors=` or in a docstring `Raises:` section. Don't declare Communication,
  Framework, or Validation errors there.
  - **Why:** those three are raised automatically by the framework or the constraint system, not
    something you opt an endpoint into.

### Writing execution errors

- **`err-define-error-per-failure-mode`**: Do define a distinct exception for every expected
  failure mode, so clients can handle each one proactively.
- **`err-surface-hardware-error-codes`**: Do surface the device's own error code or message
  inside your exception's text. Don't swallow it.
  - **Why:** the raw device error code is useful for vendor support later.
- **`err-actionable-runtime-messages`**: Do write a runtime error message that tells the operator
  what happened and what to try next, not just that something failed.
  - **Example:** "Connection lost while homing; power-cycle the device and retry", not "Error".
- **`err-no-all-errors-declared`**: Don't just list each device error in `errors=`/`Raises:`. Just list the ones
  that you expect a user to react to in that specific endpoint. A `UndefinedExecutionError` can happen in a good
  SiLA interface.
  - **Why:** declaring the expected errors explicitly is what lets a client tell "an error I can
    act on" apart from "something unexpected broke".

### Simulation vs. real mode

- **`err-start-real-mode-failed`**: Do raise a specific error (e.g. `StartRealModeFailed`) if a
  client asks to switch from simulation to real mode and the real connection can't be established.
  Don't enter real mode without a working connection; stay in simulation instead.
- **`err-hardware-error-when-disconnected`**: Do raise `HardwareError` from any method that talks
  to the device when no device is connected and `simulation_mode=False`.

## Project Structure

### The `io` / `features` split

- **`proj-features-import-from-io-not-reverse`**: Do let `features/` import from `io/`. Don't let
  `io/` import from `features/`.
  - **Why:** keeping `io/` free of SiLA dependencies means it can be tested, reused, or swapped
    independently.
- **`proj-io-has-no-sila-knowledge`**: `io/` talks to the hardware: wire protocol,
  encoding/decoding, connection management, permission checks. It has no knowledge of SiLA.
  `features/` exposes the SiLA interface and translates between user-facing concepts and protocol
  operations.
- **`proj-no-helpers-in-feature`**: Avoid adding convenience or private helper methods to a feature
  class or file. Do put the logic in `io/` and call it from the endpoint.
  - **Why:** a feature's responsibility is to define the SiLA interface and call what that
    interface needs to work, all business logic is should be handled in `io/`.
- **`proj-delegate-protocol-by-module`**: Do split a protocol into per-hardware-module delegates
  once it gets too long, instead of one large protocol class.
  - **Example:** `io/commands/pipette/`, `io/commands/core_96/`, `io/commands/heater_shaker/`,
    one submodule per physical module of the device.
- **`proj-protocol-layer-mirrors-vendor-docs`**: Do name and document `io/` commands the way the
  vendor's own internal documentation does.
  - **Why:** naming after the UniteLabs standard vocabulary happens one layer up, in `features/`,
    when translating to the SiLA interface; the protocol layer itself should stay traceable back
    to the vendor's manual.

### Configuration

- **`proj-dedicated-config-py`**: Do keep device-specific configuration in a dedicated
  `config.py`, not inline in `__init__.py`.
  - **Why:** keeps the entry point clean and the config easy to find and test on its own.
- **`proj-no-commit-config-json`**: Don't commit `config.json`.
  - **Why:** it's a development-only artifact (created by `config create` or `connector dev`),
    and there's no way to guarantee it stays in sync with `config.py`.

### Where custom exceptions live

- **`proj-hardware-errors-in-io-errors`**: Do put custom exception types for hardware-level
  errors in `io/errors.py`, close to the code that raises them.

### Debugging commands and feature extensions

- **`proj-debugging-commands-in-own-feature`**: Do put debugging and developer-helper commands in
  their own separate feature, not mixed into the connector's main functional features.
  - **Example:** jogging for calibration, sending raw commands.
- **`proj-extend-standard-feature-in-place`**: When your device needs a command or property a
  standard SiLA feature doesn't define, do add that method directly onto the same feature class,
  rather than creating a new feature or routing it into a debug-only add-on.

### Method ordering within a file

- **`proj-public-top-private-bottom`**: Do order a class top to bottom as constructor, then
  properties, then public methods, then private methods.
  - **Why:** a first-time reader wants to know what the class does before its internal details.
- **`proj-descriptive-private-method-names`**: Do give private/helper methods self-descriptive
  names.
  - **Why:** the goal is to read a file top to bottom without needing to jump around it to
    understand what's going on.

## Testing

### Simulation mode

- **`test-always-include-simulation-mode`**: Do make every connector runnable without the
  physical hardware attached. Include the `SimulationController` core feature and make the default
  startup behavior a config value.
  - **Why:** even a simulation that just returns plausible mock data enables CI, onboarding
    without hardware, and safer refactoring.
- **`test-simulate-at-protocol-level-not-feature-level`**: Do implement simulation at the
  transport protocol level, not in the feature layer.
  - **Why:** the SiLA interface gets exercised the same way whether the connector is simulated
    or talking to real hardware.
- **`test-simulation-true-by-default`**: Do default a connector's simulation mode to true.
  - **Why:** the `connector dev` CLI command relies on this assumption.
- **`test-simulation-stubs-in-io`**: Do put simulation stubs inside `io/`, not in a separate
  top-level package.

### Test layout

- **`test-mirror-package`**: Do lay out `tests/` to mirror the main package directory, with files
  named `test_*` matching the file they test.
  - **Example:** `io/protocol.py` is tested in `tests/io/test_protocol.py`.

### Testing the protocol layer

- **`test-protocol-with-stubbed-responses`**: For a device with a byte/wire-level protocol, do
  write unit tests against a stubbed protocol for every method in `io/`, mapping request bytes to
  response bytes to cover the full range of device responses, including error conditions and
  edge cases.
  - **Example:**

    ```python
    protocol = mk_stubbed_protocol(MyProtocol, {b"getSerial\r": b"0000012345\r\n"})
    ```

## Versioning & Maintainability

### Versioning

- **`ver-semantic-versioning`**: Do use semantic versioning, `MAJOR.MINOR.PATCH`.
  - **Example:** bump `MAJOR` for a breaking change to the SiLA interface (removed endpoints,
    renamed parameters, changed types); bump `MINOR` for a new, backwards-compatible endpoint or
    feature; bump `PATCH` for a bug fix or internal improvement that doesn't change the interface.
- **`ver-no-manual-version-bump`**: Don't bump the version by hand in `pyproject.toml`.
  - **Why:** releases are managed through `commitizen`.

### Code style enforcement

- **`ver-enforce-ruff-rules`**: Do follow all ruff rules selected for the project. Check manually or
  by using the pre-commit rules in place.
- **`ver-match-existing-style-when-contributing`**: When contributing to an existing connector,
  do check what style tooling is already in place and stay consistent with it.
