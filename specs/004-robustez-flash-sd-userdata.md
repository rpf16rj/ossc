# Spec 004 — Robustez: flash, SD, userdata, erros visíveis

## Contexto

Formato de userdata é itemizado (`{id, ver, size}`) — já retrocompatível. Mas:
sem CRC, dados corrompidos com a key "USRDATA" válida são aplicados verbatim, e
vários campos viram **índices de array sem check** (`group` → `group_ptr[]`,
`shmask_mode` → `shmask_data_arr_list[]`, `lumacode_*`, `item->sel.setting_str[*]`,
`def_input`/`last_input` → `input_profiles[]`). Writes de flash não são
verificados. `printf` é compilado fora em release → falhas ficam invisíveis.

P0 já implementou: timeouts I2C/flash/PCM1862, checks de `bytes_read` em
`f_read`/`SD_Read`, bounds no load de shmask/lumacode, guards de keymap zero,
fix de underflow em pcnt_field.

## Requisitos

- `[FW]` `sanitize_config()` após `read_userdata*` (flash e SD): clamp de cada
  campo de `tc`/`ts`/`last_input`/`input_profiles[]` aos ranges dos menus.
  Centralizar min/max em tabela (ou reusar os `*_MAX` de `avconfig.h`/`menu.c`).
- `[FW]` CRC32 como novo item `ude_profile_items`/`ude_initcfg_items` (ver 123):
  verificar quando presente; ausente em perfis antigos = skip silencioso.
- `[FW]` Verificação pós-write em `write_userdata()` (memcmp readback) + retorno
  de erro real; propagar "Failed" para UI.
- `[FW]` `cluster_idx[100]` em `fw_update`: ampliar para >=256 ou re-ler stream
  por `f_read`+`clst2sect` — cartões com cluster pequeno falham updates grandes
  hoje.
- `[FW]` Escrever `INIT_CONFIG_SLOT` só quando `input_profiles`/`last_input`
  mudaram (economia de erase; ~100k ciclos).
- `[FW]` Erros críticos visíveis no LCD: `err_report()` que escreve row2 + printf
  (padrão já usado em `cstm_file_load`).
- `[FW]` Detectar chip ausente via NAK real (`I2C_start` retorna `I2C_NOACK`) em
  vez de depender de 0xFF por pull-up (TVP/IT6613/PCM1862 presence checks).

## Abordagem técnica

- `sanitize_config()` roda depois de `read_userdata*` e antes de `update_cur_vm`
  ser consumido — garante que todo índice usado é válido.
- CRC: somar item com ID alto (ex. 70+), `data_size=4`; no read, se item
  presente e CRC diverge → log + fallback para defaults parciais.
- Ordem de implementação: sanitize → CRC → verify → cluster fix → err_report.

## Critérios de aceite

- Flash corrompido propositalmente (bitflip em campo indexador) não trava nem
  produz OOB — menu carrega defaults/clampados.
- `save_profile` falha visível se write não ecoar no readback.
- Update de FW funciona em cartão com cluster 2kB.

## Referências

- `userdata.c` (UDE maps, read/write flash+SD), `firmware.c` (fw_update,
  fw_update_commit), `flash.c`, `av_controller.c:499-516` (indexadores),
  `menu.c:331` (`setting_str[*]`), `sysconfig.h:27-39` (printf condicional)
