# Spec 006 — UX: timeouts, botões, auto-400p, erros

## Contexto

Constantes compiladas hoje: dwell de auto-input ~300ms (`300*(freq>>10)` em
`av_controller.c` ~1082), `STATUS_TIMEOUT_US=25ms`, `AUTO_MAX_COUNT=100`,
`AUTO_CURRENT_MAX_COUNT=6` — varredura completa de 9 entradas leva até ~30s
(issue #33). Botões do PCB são hardcoded: BTN0=próxima entrada,
BTN1=cicla scanline (#104). 400p VGA exige escolha manual 640x400 vs 720x400
(#110) — a polaridade de vsync que distingue 640x350/720x400 já é lida em
`tvp_source_sel` (`tvp7002.c` ~435) mas descartada. `printf` some em release.

## Requisitos

- `[FW]` `ts.auto_input_timeout` (100/300/600/1000ms) + scan limit em
  `settings_t` → `ude_initcfg_items` (ID 14+, ver 123) + menu_settings. (#33)
- `[FW]` `ts.btn0_func`/`ts.btn1_func`: enum de ações mapeadas p/ handlers
  existentes (próxima entrada, scanline mode, menu, OSD status, profile hotkey).
  Default = comportamento atual. (#104)
- `[FW]` `s400p_mode` ganha "Auto": quando input for HV e `TVP_SYNCSTAT` bit2
  (polaridade vsync) indicar o formato, escolher preset 640x400/720x400 —
  patch de referência existe em `wbcbz7/ossc` (branch 0.90). (#110)
- `[FW]` "H. position" em adv timing → `x_start_lb`/backporch offset em modos
  otimizados (#65 — verificar primeiro se H.backporch já cobre).
- `[FW]` Auto backporch aproximado (#106): derivar backporch de
  `hsync_width`/`h_total` medidos + razões GTF/CEA na hora do `program_mode()`,
  como opção. Heurística — documentar limitação.
- `[FW]` `err_report()`: erros críticos (SD ausente, flash falhou, userdata
  corrompida, init error indicando o chip) visíveis no LCD/OSD.
- `[FW]` "Unsupported mode" em row2 quando `get_pure_lm_mode` falha (hoje LCD
  mostra contagem de linhas nova com pipeline velho).
- `[FW]` Sweep de sampler phase assistido (#106-adjacente): modo que cicla fase
  enquanto usuário observa, para na tecla. Barato; verdadeiro auto-phase é
  pesquisa (frontend não observa pixels).

## Abordagem técnica

- Campos novos em `settings_t` (initcfg) vs `avconfig_t` (perfil): timeouts e
  botões são globais → `settings_t` + `ude_initcfg_items`.
- Auto-400p: em `program_mode()`/`get_status()`, quando `target_tvp_sync ==
  TVP_HV_A`, ler `TVP_SYNCSTAT` e escolher `MODE_640x400_70` vs `720x400_70`
  antes do preset lookup.
- Manter `LNG()` para novos textos (JP via iconv já integrado no build).

## Critérios de aceite

- Auto-input com timeout curto varre todas as entradas em tempo visivelmente
  menor; OFF mantém comportamento atual.
- BTN remapeado executa ação nova e persiste após reboot.
- VGA 640x400 e 720x400 detectados automaticamente sem tocar menu.

## Referências

- `av_controller.c` (~1081-1122 auto-input, ~1034 main), `controls.c` (~418),
  `menu.c` (~64 s400p_mode_desc), `tvp7002.c` (~435 syncstat), issues #33 #65
  #72 #104 #106 #110
