# Spec 008 — Diff dirigido OSSC Pro → Classic

## Contexto

Comparação dirigida entre `marqs85/ossc_pro` (fork Pro: Cyclone V + DDR3, scaler/framebuffer) e este fork (classic: Cyclone IV, linebuffer de 32 linhas), buscando correções em código compartilhado que não voltaram ao classic. Metodologia: diff arquivo a arquivo em `software/sys_controller/`, classificando cada diferença como fix portável, feature dependente de hardware, ou cosmético.

**Limitação:** o submodule `ic_drivers` do Pro não estava populado localmente — drivers Pro (isl51002, pcm186x, ths7353, us2066) não foram comparados corpo a corpo. TVP7002 não existe no Pro.

## Achados

### Classic já à frente do Pro (lote P0, não portar do Pro)

| Item | Classic (este fork) | Pro (upstream) |
|---|---|---|
| Poll de status do flash | `FLASH_POLL_TIMEOUT` limitado | `while(1)` sem bound |
| Bounds em `write_option_value` | checa `sel.data <= max` | indexa `setting_str[]` sem checagem |
| Buffer UART | memset após consumir | bytes residuais permanecem |
| Header de FW no update | checa `bytes_read` completo | só `!= F_OK` |

A direção correta de upstream seria oferecer essas correções ao `ossc_pro`, não o contrário.

### Backport aplicado

- **`utils.c`**: aritmética `void*` em `crc32` substituída por casts `(char*)` (forma do Pro, ISO C válido) + `-Wpointer-arith` adicionado ao `APP_CFLAGS_WARNINGS` (o Pro já o tinha). Commit `87789b7`.

### Backport recusado (registro para referência futura)

- **Import de userdata por nome** (`userdata.c` do Pro, linhas ~348-380/563-601): quando `id`/`version` batem mas `data_size` difere, o Pro casa entradas pelo campo nome e preserva `timings`/`sampler_phase`/`ar`. No classic, mudar `sizeof(video_modes_plm_default)` descarta todos os timings customizados. Recusado: upgrades de tabela são raros; risco médio de adaptar ids (classic não tem `smp_preset_t`).

### Diferenças arquiteturais (não portáveis)

- `fw_update` do Pro faz staging da imagem inteira em DRAM antes do commit; o classic não tem DRAM — o retry `f_read_cc` + `while(1)` em falha definitiva é a compensação correta.
- Scaler, A-LM, deinterlace adaptativo, EDID presets, `scl_pp_coeffs.c`, `usb_cdc_host.c`: dependem de DDR3/framebuffer/USB inexistentes no classic.

### Bugs encontrados NO OSSC Pro (reporte upstream não realizado)

1. **`av_controller.c:1310` `set_default_c_edid`** — `memset(&c_edid, 0, sizeof(c_shmask))`: `c_shmask_t` (~534B) > `c_edid_t` (~280B) → overflow de ~254B zerando globais adjacentes em todo boot via `set_default_profile(1)`.
2. **`firmware.c:88`** — `target_offset + size >= flash_size` pode sofrer wraparound de `uint32_t`; além disso não reserva a região de userdata (top 16 setores).
3. **`userdata.c:349-360`** — `read_userdata` (flash) itera `k < item_hdr.data_size` sem conferir `data_size` contra `FLASH_SECTOR_SIZE` antes do loop.

### Risco residual compartilhado

- `ip/i2c_opencores/HAL/src/i2c_opencores.c` é **idêntico** nos dois repos: polls TIP em `I2C_start`/`I2C_read`/`I2C_write`/`SPI_read`/`SPI_write` sem bound. O classic já adicionou timeouts por contagem no lote P0; melhoria futura seria timeout por timestamp (`alt_timestamp()`), consistente com `SPI_Timer_*` do ulibSD.

## Critérios de aceite

- [x] Diff dirigido executado e classificado
- [x] Backport trivial aplicado e compilado sem warnings (`-Wpointer-arith` limpo)
- [x] Achados e decisões documentados

## Referências

- `specs/README.md` — roadmap P0/P1 do fork
- Commit `87789b7` — backport dos casts + warning flag
