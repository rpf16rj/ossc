# Specs de Melhorias — ossc (fork rpf16rj)

Pesquisa produzida por auditoria multi-agente (REA-style) do código: firmware
RISC-V (`software/sys_controller`), drivers de IC (`ic_drivers/`), RTL Verilog
(`rtl/`, `ip/`) e levantamento de issues do upstream `marqs85/ossc`.

Cada spec segue o formato: **Contexto → Requisitos → Abordagem técnica → Critérios de aceite → Referências**.

Legenda: `[FW]` = somente firmware · `[RTL]` = requer síntese Quartus ·
Impacto/Esforço: Alto / Médio / Baixo.

**Ambiente:** firmware **compila e linka** no WSL com riscv64-unknown-elf-gcc
14.2 + picolibc (ver `AGENTS.md` para a receita). RTL passou em lint
(iverilog/verible) nos módulos self-contained; a síntese Quartus e o teste em
hardware continuam **não verificados**.

## Roadmap priorizado

### P0 — Quick wins de correção (implementado neste lote)

Status: ✅ implementado · ⚠️ parcial · ⬜ pendente

| Item | Status | Origem | Notas |
|---|---|---|---|
| Deref OOB `shmask_data_arr_list[-1]` quando perfil tem `shmask_mode=0` | ✅ | `av_controller.c` | `invalidate_loaded_arrays()` usa -1; guard agora valida faixa |
| `sl_cust_c_str[6]` lido como `[10]` (sub-colunas 7-10 liam `iv_x/iv_y/mask_*`) | ✅ | `av_controller.c`, `avconfig.h` | campo alargado p/ `[10]`; UDE id 31 bump p/ ver 123; menu ganhou itens 7-10 |
| `load_shmask()` sem bounds em `iv_x/iv_y` vindos de arquivo → OOB em `c_shmask` e `sc->shmask_data_array` | ✅ | `menu.c` | clamp/reject de dimensões 1-16 e de linhas excedentes |
| Buffer UART: bytes residuais → re-comandos fantasmas; buffer cheio sem `\n` → livelock do RX | ✅ | `controls.c` | reset incondicional + memset do buffer |
| Keymap zero → `remote_code==0`/`btn_vec==0` casam com `rc_keymap[i]==0` → teclas fantasmas (inclui auto-confirmar flash de FW) | ✅ | `controls.c`, `firmware.c` | guards `remote_code &&` / `btn_vec &&` em todas as comparações |
| `write_option_value`: índice fora de faixa em `setting_str[]` se valor de seleção corrompido | ✅ | `menu.c` | clamp por `item->sel.max` com fallback "Invalid" |
| Underflow unsigned `cm.pcnt_field - PCNT_TOLERANCE` → `MODE_CHANGE` espúrio em loop | ✅ | `av_controller.c` | comparação rescrita sem wrap |
| `f_read` de header de FW sem checar `bytes_read` | ✅ | `firmware.c` | rejeita arquivo truncado |
| `fw_update_commit` ignora falha de `SD_Read` → grava lixo na flash (brick) | ✅ | `firmware.c` | retry 4x + aborta; copy loop não ultrapassa `bytes_read` |
| AVI infoframe sempre anuncia ITU601 (`ITU709=0` fixo) | ✅ | `av_controller.c` | ITU709 derivado dos timings de saída (v_active≥720 ou interlaced ≥540) |
| Polling TIP do I2C opencores sem timeout → MCU trava se barramento falhar | ✅ | `i2c_opencores.c` | timeout por contagem (~10k iterações) em start/read/write/SPI |
| `pcm_set_stereo_mode` busy-wait sem timeout → trava se PCM1862 sumir | ✅ | `pcm1862.c` | bounded poll |
| `ths_source_sel` descarta parâmetro `lpf` (linha comentada) | ✅ | `ths7353.c` | LPF agora aplicado (preserva comportamento: chamadores já chamam set_lpf depois) |
| `flash_write_protect`/`flash_sector_erase` polls `while(1)` → freeze permanente | ✅ | `flash.c` | bounded poll ~timeout |
| `panasonic_adjust` truncado p/ 0 (`8'd128` em wire[6:0]) → hack Panasonic morto | ✅ | `scanconverter.v` | wire alargado p/ `[7:0]` |
| Reverse-LPF quebrado: multiply signed×unsigned → diffs negativos viram garbage | ✅ | `tvp7002_frontend.v` | `$signed({1'b0, MISC_REV_LPF_STR})` nos 3 canais |
| `osd_generator_top.sv`: índice negativo em `RSEC_ENABLE` quando `ypos_scaled<8`; índice 8-bit em array 8×8 sem slice | ✅ | `osd_generator_top.sv` | guard + slice `[2:0]` |
| `lat_tester` `mode_synced` decl `[2:0]` vs wire `[1:0]` | ✅ | `lat_tester.v` | decl corrigida |
| `ir_rcv`: `databuf[32-bits_detected]` pode indexar -1 | ✅ | `ir_rcv.v` | guard `bits_detected <= 32`; literais 16'h |
| `interlace_flag` cruza clk27→PCLK_CAP sem sincronizador | ✅ | `tvp7002_frontend.v` | 2FF no domínio PCLK_i |
| `lt_active`/`pll_activeclock`/`pll_locked` assíncronos em `ossc.v` | ✅ | `ossc.v` | 2FF syncs |

### P1 — Features de firmware (specs 001-007)

| Spec | Resumo | Impacto/Esforço |
|---|---|---|
| [001](001-sync-robustez-e-transicoes.md) | Filtro de glitch de hsync (bit em misc_config), persistência do `frame_change_resync`, issues #126/#132/#135 | Alto / Médio |
| [002](002-tvp7002-analog-sweep.md) | REA sweep TVP7002: `TVP_ADCSETUP` (TODO no código), coarse offset/clamp, telemetria ALC/linhas, STC bias do THS7353 | Médio-Alto / Médio |
| [003](003-hdmi-tx-audio-e-avmute.md) | Recuperação OSF_LOCK (áudio some — #26/#34), TMDS swing/AFE, HPD/RxSense monitor, poda de ~2.5k linhas de dead code | Alto / Médio-Alto |
| [004](004-robustez-flash-sd-userdata.md) | CRC32 + sanitize em userdata, verificação pós-write de flash, limite `cluster_idx[100]`, erros visíveis no LCD | Alto / Médio |
| [005](005-masks-posproc-e-aspect.md) | Duas máscaras H independentes (#95/#133), composite blend (#103), bit-depth/dither (#42), square PAR 384/512 (#37), `pm_288p` separado (#85) | Médio-Alto / Médio-Alto |
| [006](006-ux-controles-timeout.md) | Timeout de auto-input configurável (#33), botões PCB configuráveis (#104), auto 400p por polaridade (#110), posição H (#65) | Médio / Médio |
| [007](007-deinterlace.md) | Ligar hooks dormentes `LM_DEINT_MODE`/`NIR_EVEN_OFFSET` (#132), deinterlace interpolado (#100) | Médio / Alto |

### Fora de escopo / somente documentar

- Áudio em modo DVI (#97): data islands não existem em DVI por spec — documentar
- Anamorphic 4:3→16:9 (#99), fractional sampling (#59): precisam de scaler/framebuffer → território OSSC Pro
- Backports do OSSC Pro: A-LM, scaler, EDID presets — HW incompatível (linebuf 32 linhas, sem DDR)
- HDCP no IT6613: ~1200 linhas mortas e sem licença de chaves — remover, não habilitar

## Reclamações da comunidade → onde são endereçadas

| Reclamação | Spec |
|---|---|
| Sync loss em fontes problemáticas (Uzebox #126, 32X #135) | 001 + 002 |
| Glitch em transição 240p↔480i (#132) | 001 + 007 |
| Áudio cortando / some (#26, #34) | 003 |
| Áudio em DVI (#97) | fora de escopo (documentado em 003) |
| 400p VGA não detecta (#110) | 006 |
| Backporch/auto ajuste (#106) | 006 |
| Máscaras assimétricas / bordas 4:3 (#95, #133) | 005 |
| Composite blending (#103), bit depth (#42) | 005 |
| Sampling separado 240p/288p (#85) | 005 |
| Posição H em modos otimizados (#65) | 006 |
| Timeout de detecção de entrada (#33) | 006 |
| Botões do PCB fixos (#104) | 006 |
| Deinterlace melhor (#100) | 007 |
| UI/OSD enhancements (#72) | 006 |
| PC Engine palette (#90) | 002 (via ram de paleta lumacode) |
| 8.x→1.x regressões de VGA (#28) | verificar com Adv. timing; provável stale |
