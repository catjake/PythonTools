import util
import copy
import string
from mFileDialog import selectDialog, m_selectDialog, selectDirectory, user_entry_dialog, question
from Tkinter import Tk
from time import time, sleep
import enVision_tools as enV

DefaultSignalHeader=[]
F751980_SH_analogue=[]
wanda_signal_header=[]
wanda_analog_signal_header=[]
marika_signal_header=[]
Analog2Wanda=[]
Default2Marika=[]
Default2Wanda=[]
Interconnect=[]

def initialize_globals():
    global DefaultSignalHeader
    DefaultSignalHeader = ['a1', 'a10', 'a11', 'a12', 'a13', 'a14', 'a15', 'a16', 'a17', 'a18', 'a19', 'a2', 'a20', 'a21', 'a22', \
    'a23', 'a24', 'a25', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9', 'adcstr', 'antsw0', 'antsw1', 'antsw2', 'antsw3', 'bandsel', 'cid0', \
    'cid1', 'cid2', 'cid3', 'cid4', 'cid5', 'cid6', 'cid7', 'cihsync', 'cipclk', 'cires_n', 'civsync', 'clkreq', 'cs0_n', 'cs1_n', \
    'cs2_n', 'cs3_n', 'd0', 'd1', 'd10', 'd11', 'd12', 'd13', 'd14', 'd15', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8', 'd9', 'dacclk', \
    'dacdat', 'dacstr', 'dclk', 'dirmod0', 'dirmod1', 'dirmod2', 'dirmod3', 'dirmodclk', 'etmpstat0', 'etmpstat1', 'etmpstat2', 'etmtclk', \
    'etmtpkt0', 'etmtpkt1', 'etmtpkt2', 'etmtpkt3', 'etmtpkt4', 'etmtpkt5', 'etmtpkt6', 'etmtpkt7', 'etmtsync', 'gpio00', 'gpio01', \
    'gpio02', 'gpio03', 'gpio04', 'gpio05', 'gpio06', 'gpio07', 'gpio10', 'gpio11', 'gpio12', 'gpio13', 'gpio14', 'gpio15', 'gpio16', \
    'gpio17', 'gpio20', 'gpio21', 'gpio22', 'gpio23', 'gpio24', 'gpio25', 'gpio26', 'gpio27', 'gpio30', 'gpio31', 'gpio32', 'gpio33', \
    'gpio34', 'gpio35', 'gpio36', 'gpio37', 'gpio40', 'gpio41', 'gpio42', 'gpio43', 'gpio44', 'gpio45', 'gpio46', 'gpio47', 'hsslrx', \
    'hsslrxclk', 'hssltx', 'hssltxclk', 'i2cscl0', 'i2cscl1', 'i2csda0', 'i2csda1', 'idata', 'irq0_n', 'irq1_n', 'isevent_n', 'issync_n', \
    'keyin0_n', 'keyin1_n', 'keyin2_n', 'keyin3_n', 'keyin4_n', 'keyout0_n', 'keyout1_n', 'keyout2_n', 'keyout3_n', 'keyout4_n', \
    'keyout5_n', 'mclk_M', 'memadv_n', 'membe0_n', 'membe1_n', 'memclk', 'memclkret', 'memwait_n', 'mmcclk', 'mmccmd', 'mmccmddir', \
    'mmcdat0', 'mmcdat1', 'mmcdat2', 'mmcdat3', 'mmcdatdir', 'nf_ale', 'nf_cle', 'nf_cs_n', 'nf_d0', 'nf_d1', 'nf_d2', 'nf_d3', 'nf_d4', \
    'nf_d5', 'nf_d6', 'nf_d7', 'nf_rb', 'nf_re_n', 'nf_we_n', 'oe_n', 'pcmclk', 'pcmdata', 'pcmdatb', 'pcmsyn', 'pdic0', 'pdic1', 'pdic2', \
    'pdic3', 'pdic4', 'pdic5', 'pdid0', 'pdid1', 'pdid2', 'pdid3', 'pdid4', 'pdid5', 'pdid6', 'pdid7', 'pdires_n', 'pwrreq0_n', \
    'pwrreq1_n', 'qdata', 'resout0_n', 'resout1_n', 'resout2_n', 'respow_n', 'rfclk', 'rfdat', 'rfstr', 'rtcbdis_n', 'rtcclk', 'rtcdcon', \
    'rtcin', 'rtck', 'rtcout', 'sdr_cas_n', 'sdr_cke', 'sdr_clk', 'sdr_clkret', 'sdr_cs_n', 'sdr_ras_n', 'service_n', 'simclk', 'simdat', \
    'simrst_n', 'sysclk0', 'sysclk1', 'sysclk2', 'tck_M', 'tdi_M', 'tdo_M', 'temu0_n_M', 'temu1_n_M', 'tms_M', 'trst_n_M', 'usbdm', \
    'usbdp', 'usboe', 'usbpuen', 'usbsusp', 'vinithi', 'we_n', 'ADC_I_IN', 'ADC_I_IN_INV', 'ADC_Q_IN', 'ADC_Q_IN_INV', 'ADC_RXEXTREF_N', \
    'ADC_RXEXTREF_P', 'ANALOG_ENABLE', 'APLL_ATEST1', 'APLL_BYPASS', 'BG_REF', 'BOOTMODE_0', 'BOOTMODE_1', 'BOOTMODE_2', 'BOOTMODE_3', \
    'CLK32', 'CPU_CLKOUT', 'CPU_IACK', 'CPU_IRQ_0', 'CPU_IRQ_1', 'CPU_XF', 'CS_BYPASS', 'DAC_CLK', 'DAC_DAT', 'DAC_I_OUT', \
    'DAC_I_OUT_INV', 'DAC_Q_OUT', 'DAC_Q_OUT_INV', 'DAC_STR', 'DAC_TXEXTRES', 'EMIF_A_1', 'EMIF_A_10', 'EMIF_A_11', 'EMIF_A_12', \
    'EMIF_A_13', 'EMIF_A_14', 'EMIF_A_15', 'EMIF_A_16', 'EMIF_A_17', 'EMIF_A_18', 'EMIF_A_19', 'EMIF_A_2', 'EMIF_A_20', 'EMIF_A_21', \
    'EMIF_A_22', 'EMIF_A_23', 'EMIF_A_3', 'EMIF_A_4', 'EMIF_A_5', 'EMIF_A_6', 'EMIF_A_7', 'EMIF_A_8', 'EMIF_A_9', 'EMIF_ARE_N', \
    'EMIF_AREADY', 'EMIF_AWE_N', 'EMIF_D_0', 'EMIF_D_1', 'EMIF_D_10', 'EMIF_D_11', 'EMIF_D_12', 'EMIF_D_13', 'EMIF_D_14', 'EMIF_D_15', \
    'EMIF_D_16', 'EMIF_D_17', 'EMIF_D_18', 'EMIF_D_19', 'EMIF_D_2', 'EMIF_D_20', 'EMIF_D_21', 'EMIF_D_22', 'EMIF_D_23', 'EMIF_D_24', \
    'EMIF_D_25', 'EMIF_D_26', 'EMIF_D_27', 'EMIF_D_28', 'EMIF_D_29', 'EMIF_D_3', 'EMIF_D_30', 'EMIF_D_31', 'EMIF_D_4', 'EMIF_D_5', \
    'EMIF_D_6', 'EMIF_D_7', 'EMIF_D_8', 'EMIF_D_9', 'EMU0_W', 'EMU1_W', 'EXT_FRAME_STROBE', 'EXT_MEM_UBUS_10', 'EXT_MEM_UBUS_11', \
    'EXT_MEM_UBUS_12', 'GPO_0', 'GPO_1', 'GPO_2', 'GPO_3', 'GPO_4', 'GPO_5', 'GPO_6', 'GPO_7', 'HCLK', 'TCK_W', 'TDI_W', 'TDO_W', \
    'TMS_W', 'TRST_N_W', 'MCLK_W', 'RADIO_CLK', 'RADIO_DAT', 'RADIO_STR', 'TESTMODE', 'UART_RX', 'UART_TX']

    global F751980_SH_analogue
    F751980_SH_analogue = ['HCLK', 'EMIF_D_4', 'EMIF_D_0', 'EMIF_D_1', 'EMIF_D_2', 'EMIF_D_3', 'GPO_2', 'GPO_3', 'APLL_ATEST1', \
    'GPO_4', 'GPO_5', 'TRST_N_W', 'TCK_W', 'TMS_W', 'TDI_W', 'TDO_W', 'EMU0_W', 'EMU1_W', 'APLL_BYPASS', 'CS_BYPASS', 'TESTMODE', \
    'ANALOG_ENABLE', 'MCLK_W', 'CLK32', 'resout1_n', 'issync_n', 'isevent_n', 'clkreq', 'EMIF_AREADY', 'EMIF_D_14', 'EMIF_D_15', \
    'EMIF_D_20', 'EMIF_D_21', 'EMIF_D_26', 'EMIF_D_27', 'EMIF_A_1', 'EMIF_A_2', 'EMIF_A_3', 'EMIF_A_4', 'EMIF_A_5', 'EMIF_A_6', \
    'EMIF_A_7', 'EMIF_A_8', 'EMIF_A_9', 'EMIF_A_18', 'EMIF_A_10', 'EMIF_A_11', 'EMIF_A_12', 'EMIF_A_13', 'EMIF_A_14', 'EMIF_A_15', \
    'EMIF_A_16', 'EMIF_A_17', 'EMIF_A_19', 'EMIF_A_20', 'EMIF_A_21', 'EMIF_A_22', 'EMIF_A_23', 'GPO_0', 'GPO_1', 'CPU_CLKOUT', \
    'EXT_FRAME_STROBE', 'adcstr', 'CPU_XF', 'DAC_CLK', 'RADIO_STR', 'RADIO_CLK', 'RADIO_DAT', 'hsslrxclk', 'hsslrx', 'hssltxclk', \
    'hssltx', 'UART_TX', 'UART_RX', 'DAC_TXEXTRES', 'DAC_I_OUT', 'DAC_I_OUT_INV', 'DAC_Q_OUT', 'DAC_Q_OUT_INV', 'ADC_RXEXTREF_N', \
    'ADC_RXEXTREF_P', 'BG_REF', 'ADC_I_IN', 'ADC_I_IN_INV', 'ADC_Q_IN', 'ADC_Q_IN_INV', 'BOOTMODE_0', 'BOOTMODE_1', 'BOOTMODE_2', \
    'BOOTMODE_3', 'GPO_6', 'GPO_7', 'EMIF_D_19', 'EMIF_D_18', 'EMIF_D_17', 'EMIF_D_16', 'EMIF_D_25', 'EMIF_D_24', 'EMIF_D_23', \
    'EMIF_D_22', 'CPU_IACK', 'EMIF_D_31', 'EMIF_D_30', 'EMIF_D_29', 'EMIF_D_28', 'EXT_MEM_UBUS_12', 'EXT_MEM_UBUS_11', 'EXT_MEM_UBUS_10', \
    'CPU_IRQ_0', 'CPU_IRQ_1', 'EMIF_D_11', 'EMIF_D_12', 'EMIF_D_13', 'EMIF_AWE_N', 'DAC_STR', 'DAC_DAT', 'EMIF_ARE_N', 'EMIF_D_5', \
    'EMIF_D_9', 'EMIF_D_10', 'EMIF_D_8', 'EMIF_D_7', 'EMIF_D_6', 'SMS_TRIG_P', 'SMS_TRIG_N']

    global wanda_signal_header
    wanda_signal_header = ['resout1_n', 'ADC_I_IN', \
    'ADC_I_IN_INV', 'ADC_Q_IN', 'ADC_Q_IN_INV', 'ADC_RXEXTREF_N', 'ADC_RXEXTREF_P', 'ANALOG_ENABLE', 'APLL_ATEST1', 'APLL_BYPASS', \
    'BG_REF', 'BOOTMODE_0', 'BOOTMODE_1', 'BOOTMODE_2', 'BOOTMODE_3', 'CLK32', 'CPU_CLKOUT', 'CPU_IACK', 'CPU_IRQ_0', 'CPU_IRQ_1', \
    'CPU_XF', 'CS_BYPASS', 'DAC_CLK', 'DAC_DAT', 'DAC_I_OUT', 'DAC_I_OUT_INV', 'DAC_Q_OUT', 'DAC_Q_OUT_INV', 'DAC_STR', 'DAC_TXEXTRES', \
    'EMIF_A_1', 'EMIF_A_10', 'EMIF_A_11', 'EMIF_A_12', 'EMIF_A_13', 'EMIF_A_14', 'EMIF_A_15', 'EMIF_A_16', 'EMIF_A_17', 'EMIF_A_18', \
    'EMIF_A_19', 'EMIF_A_2', 'EMIF_A_20', 'EMIF_A_21', 'EMIF_A_22', 'EMIF_A_23', 'EMIF_A_3', 'EMIF_A_4', 'EMIF_A_5', 'EMIF_A_6', 'EMIF_A_7', \
    'EMIF_A_8', 'EMIF_A_9', 'EMIF_ARE_N', 'EMIF_AREADY', 'EMIF_AWE_N', 'EMIF_D_0', 'EMIF_D_1', 'EMIF_D_10', 'EMIF_D_11', 'EMIF_D_12', 'EMIF_D_13', \
    'EMIF_D_14', 'EMIF_D_15', 'EMIF_D_16', 'EMIF_D_17', 'EMIF_D_18', 'EMIF_D_19', 'EMIF_D_2', 'EMIF_D_20', 'EMIF_D_21', 'EMIF_D_22', 'EMIF_D_23', \
    'EMIF_D_24', 'EMIF_D_25', 'EMIF_D_26', 'EMIF_D_27', 'EMIF_D_28', 'EMIF_D_29', 'EMIF_D_3', 'EMIF_D_30', 'EMIF_D_31', 'EMIF_D_4', 'EMIF_D_5', \
    'EMIF_D_6', 'EMIF_D_7', 'EMIF_D_8', 'EMIF_D_9', 'EMU0_W', 'EMU1_W', 'EXT_FRAME_STROBE', 'EXT_MEM_UBUS_10', 'EXT_MEM_UBUS_11', \
    'EXT_MEM_UBUS_12', 'GPO_0', 'GPO_1', 'GPO_2', 'GPO_3', 'GPO_4', 'GPO_5', 'GPO_6', 'GPO_7', 'HCLK', 'TCK_W', 'TDI_W', 'TDO_W', 'TMS_W', \
    'TRST_N_W', 'MCLK_W', 'RADIO_CLK', 'RADIO_DAT', 'RADIO_STR', 'TESTMODE', 'UART_RX', 'UART_TX']

    global wanda_analog_signal_header
    wanda_analog_signal_header = ['HCLK', 'EMIF_D_4', 'EMIF_D_0', 'EMIF_D_1', 'EMIF_D_2', 'EMIF_D_3', 'GPO_2', 'GPO_3', 'APLL_ATEST1', \
    'GPO_4', 'GPO_5', 'TRST_N_W', 'TCK_W', 'TMS_W', 'TDI_W', 'TDO_W', 'EMU0_W', 'EMU1_W', 'APLL_BYPASS', 'CS_BYPASS', 'TESTMODE', \
    'ANALOG_ENABLE', 'MCLK_W', 'CLK32', 'resout1_n', 'issync_n', 'isevent_n', 'EMIF_AREADY', 'EMIF_D_14', 'EMIF_D_15', \
    'EMIF_D_20', 'EMIF_D_21', 'EMIF_D_26', 'EMIF_D_27', 'EMIF_A_1', 'EMIF_A_2', 'EMIF_A_3', 'EMIF_A_4', 'EMIF_A_5', 'EMIF_A_6', \
    'EMIF_A_7', 'EMIF_A_8', 'EMIF_A_9', 'EMIF_A_18', 'EMIF_A_10', 'EMIF_A_11', 'EMIF_A_12', 'EMIF_A_13', 'EMIF_A_14', 'EMIF_A_15', \
    'EMIF_A_16', 'EMIF_A_17', 'EMIF_A_19', 'EMIF_A_20', 'EMIF_A_21', 'EMIF_A_22', 'EMIF_A_23', 'GPO_0', 'GPO_1', 'CPU_CLKOUT', \
    'EXT_FRAME_STROBE', 'CPU_XF', 'DAC_CLK', 'RADIO_STR', 'RADIO_CLK', 'RADIO_DAT', \
    'UART_TX', 'UART_RX', 'DAC_TXEXTRES', 'DAC_I_OUT', 'DAC_I_OUT_INV', 'DAC_Q_OUT', 'DAC_Q_OUT_INV', 'ADC_RXEXTREF_N', \
    'ADC_RXEXTREF_P', 'BG_REF', 'ADC_I_IN', 'ADC_I_IN_INV', 'ADC_Q_IN', 'ADC_Q_IN_INV', 'BOOTMODE_0', 'BOOTMODE_1', 'BOOTMODE_2', \
    'BOOTMODE_3', 'GPO_6', 'GPO_7', 'EMIF_D_19', 'EMIF_D_18', 'EMIF_D_17', 'EMIF_D_16', 'EMIF_D_25', 'EMIF_D_24', 'EMIF_D_23', \
    'EMIF_D_22', 'CPU_IACK', 'EMIF_D_31', 'EMIF_D_30', 'EMIF_D_29', 'EMIF_D_28', 'EXT_MEM_UBUS_12', 'EXT_MEM_UBUS_11', 'EXT_MEM_UBUS_10', \
    'CPU_IRQ_0', 'CPU_IRQ_1', 'EMIF_D_11', 'EMIF_D_12', 'EMIF_D_13', 'EMIF_AWE_N', 'DAC_STR', 'DAC_DAT', 'EMIF_ARE_N', 'EMIF_D_5', \
    'EMIF_D_9', 'EMIF_D_10', 'EMIF_D_8', 'EMIF_D_7', 'EMIF_D_6', 'SMS_TRIG_P', 'SMS_TRIG_N']

    global marika_signal_header
    marika_signal_header = ['a1', 'a10', 'a11', 'a12', 'a13', 'a14', 'a15', 'a16', 'a17', 'a18', 'a19', 'a2', 'a20', 'a21', 'a22', \
    'a23', 'a24', 'a25', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9', 'adcstr', 'antsw0', 'antsw1', 'antsw2', 'antsw3', 'bandsel', 'cid0', \
    'cid1', 'cid2', 'cid3', 'cid4', 'cid5', 'cid6', 'cid7', 'cihsync', 'cipclk', 'cires_n', 'civsync', 'clkreq', 'cs0_n', 'cs1_n', \
    'cs2_n', 'cs3_n', 'd10', 'd11', 'd12', 'd13', 'd14', 'd15', 'd2', 'd9', 'dacclk', 'dacdat', \
    'dacstr', 'dclk', 'dirmod0', 'dirmod1', 'dirmod2', 'dirmod3', 'dirmodclk', 'etmpstat0', 'etmpstat1', 'etmpstat2', 'etmtclk', \
    'etmtpkt0', 'etmtpkt1', 'etmtpkt2', 'etmtpkt3', 'etmtpkt4', 'etmtpkt5', 'etmtpkt6', 'etmtpkt7', 'etmtsync', 'gpio00', 'gpio01', \
    'gpio02', 'gpio03', 'gpio04', 'gpio05', 'gpio06', 'gpio07', 'gpio10', 'gpio11', 'gpio12', 'gpio13', 'gpio14', 'gpio15', 'gpio16', \
    'gpio17', 'gpio20', 'gpio21', 'gpio22', 'gpio23', 'gpio24', 'gpio25', 'gpio26', 'gpio27', 'gpio30', 'gpio31', 'gpio32', 'gpio33', \
    'gpio34', 'gpio35', 'gpio36', 'gpio37', 'gpio40', 'gpio41', 'gpio42', 'gpio43', 'gpio44', 'gpio45', 'gpio46', 'gpio47', 'hsslrx', \
    'hsslrxclk', 'hssltx', 'hssltxclk', 'i2cscl0', 'i2cscl1', 'i2csda0', 'i2csda1', 'idata', 'irq0_n', 'irq1_n', 'isevent_n', 'issync_n', \
    'keyin0_n', 'keyin1_n', 'keyin2_n', 'keyin3_n', 'keyin4_n', 'keyout0_n', \
    'keyout1_n', 'keyout2_n', 'keyout3_n', 'keyout4_n', 'keyout5_n', 'mclk_M', 'memadv_n', 'membe0_n', 'membe1_n', 'memclk', 'memclkret', \
    'memwait_n', 'mmcclk', 'mmccmd', 'mmccmddir', 'mmcdat0', 'mmcdat1', 'mmcdat2', 'mmcdat3', 'mmcdatdir', 'nf_ale', 'nf_cle', 'nf_cs_n', \
    'nf_d0', 'nf_d1', 'nf_d2', 'nf_d3', 'nf_d4', 'nf_d5', 'nf_d6', 'nf_d7', 'nf_rb', 'nf_re_n', 'nf_we_n', 'oe_n', 'pcmclk', 'pcmdata', \
    'pcmdatb', 'pcmsyn', 'pdic0', 'pdic1', 'pdic2', 'pdic3', 'pdic4', 'pdic5', 'pdid0', 'pdid1', 'pdid2', 'pdid3', 'pdid4', 'pdid5', \
    'pdid6', 'pdid7', 'pdires_n', 'pwrreq0_n', 'pwrreq1_n', 'qdata', 'resout0_n', 'resout2_n', 'respow_n', 'rfclk', 'rfdat', 'rfstr', \
    'rtcbdis_n', 'rtcclk', 'rtcdcon', 'rtcin', 'rtck', 'rtcout', 'sdr_cas_n', 'sdr_cke', 'sdr_clk', 'sdr_clkret', 'sdr_cs_n', 'sdr_ras_n', \
    'service_n', 'simclk', 'simdat', 'simrst_n', 'sysclk0', 'sysclk1', 'sysclk2', 'tck_M', 'tdi_M', 'tdo_M', 'temu0_n_M', 'temu1_n_M', \
    'tms_M', 'trst_n_M', 'usbdm', 'usbdp', 'usboe', 'usbpuen', 'usbsusp', 'vinithi', 'we_n']

    global Analog2Wanda
    Analog2Wanda = ['adcstr', 'clkreq', 'hsslrxclk', 'hsslrx', 'hssltxclk', 'hssltx', 'issync_n', 'isevent_n']

    global Default2Marika
    Default2Marika = ['ADC_I_IN', 'ADC_I_IN_INV', 'ADC_Q_IN', 'ADC_Q_IN_INV', 'ADC_RXEXTREF_N', 'ADC_RXEXTREF_P', \
    'ANALOG_ENABLE', 'APLL_ATEST1', 'APLL_BYPASS', 'BG_REF', 'BOOTMODE_0', 'BOOTMODE_1', 'BOOTMODE_2', \
    'BOOTMODE_3', 'CLK32', 'CPU_CLKOUT', 'CPU_IACK', 'CPU_IRQ_0', 'CPU_IRQ_1', 'CPU_XF', 'CS_BYPASS', 'd0', 'd1', 'd3', 'd4', \
    'd5', 'd6', 'd7', 'd8', 'DAC_CLK', 'DAC_DAT', 'DAC_I_OUT', \
    'DAC_I_OUT_INV', 'DAC_Q_OUT', 'DAC_Q_OUT_INV', 'DAC_STR', 'DAC_TXEXTRES', 'EMIF_A_1', 'EMIF_A_10', 'EMIF_A_11', 'EMIF_A_12', \
    'EMIF_A_13', 'EMIF_A_14', 'EMIF_A_15', 'EMIF_A_16', 'EMIF_A_17', 'EMIF_A_18', 'EMIF_A_19', 'EMIF_A_2', 'EMIF_A_20', 'EMIF_A_21', \
    'EMIF_A_22', 'EMIF_A_23', 'EMIF_A_3', 'EMIF_A_4', 'EMIF_A_5', 'EMIF_A_6', 'EMIF_A_7', 'EMIF_A_8', 'EMIF_A_9', 'EMIF_AREADY', \
    'EMIF_ARE_N', 'EMIF_AWE_N', 'EMIF_D_0', 'EMIF_D_1', 'EMIF_D_10', 'EMIF_D_11', 'EMIF_D_12', 'EMIF_D_13', 'EMIF_D_14', 'EMIF_D_15', \
    'EMIF_D_16', 'EMIF_D_17', 'EMIF_D_18', 'EMIF_D_19', 'EMIF_D_2', 'EMIF_D_20', 'EMIF_D_21', 'EMIF_D_22', 'EMIF_D_23', 'EMIF_D_24', \
    'EMIF_D_25', 'EMIF_D_26', 'EMIF_D_27', 'EMIF_D_28', 'EMIF_D_29', 'EMIF_D_3', 'EMIF_D_30', 'EMIF_D_31', 'EMIF_D_4', 'EMIF_D_5', \
    'EMIF_D_6', 'EMIF_D_7', 'EMIF_D_8', 'EMIF_D_9', 'EMU0_W', 'EMU1_W', 'EXT_FRAME_STROBE', 'EXT_MEM_UBUS_10', 'EXT_MEM_UBUS_11', \
    'EXT_MEM_UBUS_12', 'GPO_0', 'GPO_1', 'GPO_2', 'GPO_3', 'GPO_4', 'GPO_5', 'GPO_6', 'GPO_7', 'HCLK', \
    'MCLK_W', 'RADIO_CLK', 'RADIO_DAT', 'RADIO_STR', 'resout1_n', \
    'TCK_W', 'TDI_W', 'TDO_W', 'TESTMODE', 'TMS_W', 'TRST_N_W', 'UART_RX', 'UART_TX']

    global Default2Wanda
    Default2Wanda = ['a1', 'a10', 'a11', 'a12', 'a13', 'a14', 'a15', 'a16', 'a17', 'a18', 'a19', 'a2', 'a20', 'a21', 'a22', 'a23', \
    'a24', 'a25', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9', 'adcstr', 'antsw0', 'antsw1', 'antsw2', 'antsw3', 'bandsel', 'cid0', 'cid1', \
    'cid2', 'cid3', 'cid4', 'cid5', 'cid6', 'cid7', 'cihsync', 'cipclk', 'cires_n', 'civsync', 'clkreq', 'cs0_n', 'cs1_n', 'cs2_n', \
    'cs3_n', 'd0', 'd1', 'd10', 'd11', 'd12', 'd13', 'd14', 'd15', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8', 'd9', 'dacclk', 'dacdat', \
    'dacstr', 'dclk', 'dirmod0', 'dirmod1', 'dirmod2', 'dirmod3', 'dirmodclk', 'etmpstat0', 'etmpstat1', 'etmpstat2', 'etmtclk', \
    'etmtpkt0', 'etmtpkt1', 'etmtpkt2', 'etmtpkt3', 'etmtpkt4', 'etmtpkt5', 'etmtpkt6', 'etmtpkt7', 'etmtsync', 'gpio00', 'gpio01', \
    'gpio02', 'gpio03', 'gpio04', 'gpio05', 'gpio06', 'gpio07', 'gpio10', 'gpio11', 'gpio12', 'gpio13', 'gpio14', 'gpio15', 'gpio16', \
    'gpio17', 'gpio20', 'gpio21', 'gpio22', 'gpio23', 'gpio24', 'gpio25', 'gpio26', 'gpio27', 'gpio30', 'gpio31', 'gpio32', 'gpio33', \
    'gpio34', 'gpio35', 'gpio36', 'gpio37', 'gpio40', 'gpio41', 'gpio42', 'gpio43', 'gpio44', 'gpio45', 'gpio46', 'gpio47', 'hsslrx', \
    'hsslrxclk', 'hssltx', 'hssltxclk', 'i2cscl0', 'i2cscl1', 'i2csda0', 'i2csda1', 'idata', 'irq0_n', 'irq1_n', 'isevent_n', \
    'issync_n', 'keyin0_n', 'keyin1_n', 'keyin2_n', 'keyin3_n', 'keyin4_n', 'keyout0_n', 'keyout1_n', 'keyout2_n', 'keyout3_n', \
    'keyout4_n', 'keyout5_n', 'mclk_M', 'memadv_n', 'membe0_n', 'membe1_n', 'memclk', 'memclkret', 'memwait_n', 'mmcclk', 'mmccmd', \
    'mmccmddir', 'mmcdat0', 'mmcdat1', 'mmcdat2', 'mmcdat3', 'mmcdatdir', 'nf_ale', 'nf_cle', 'nf_cs_n', 'nf_d0', 'nf_d1', 'nf_d2', \
    'nf_d3', 'nf_d4', 'nf_d5', 'nf_d6', 'nf_d7', 'nf_rb', 'nf_re_n', 'nf_we_n', 'oe_n', 'pcmclk', 'pcmdata', 'pcmdatb', 'pcmsyn', \
    'pdic0', 'pdic1', 'pdic2', 'pdic3', 'pdic4', 'pdic5', 'pdid0', 'pdid1', 'pdid2', 'pdid3', 'pdid4', 'pdid5', 'pdid6', 'pdid7', \
    'pdires_n', 'pwrreq0_n', 'pwrreq1_n', 'qdata', 'resout0_n', 'resout2_n', 'respow_n', 'rfclk', 'rfdat', 'rfstr', 'rtcbdis_n', \
    'rtcclk', 'rtcdcon', 'rtcin', 'rtck', 'rtcout', 'sdr_cas_n', 'sdr_cke', 'sdr_clk', 'sdr_clkret', 'sdr_cs_n', 'sdr_ras_n', \
    'service_n', 'simclk', 'simdat', 'simrst_n', 'sysclk0', 'sysclk1', 'sysclk2', 'tck_M', 'tdi_M', 'tdo_M', 'temu0_n_M', \
    'temu1_n_M', 'tms_M', 'trst_n_M', 'usbdm', 'usbdp', 'usboe', 'usbpuen', 'usbsusp', 'vinithi', 'we_n']
#to modify a pin list and reduce the members, copy into a_string
def remove_pins(a_string,pins_to_remove):
    '''new_string = remove_pins(a_strin,pins_to_remove)
    a_string = waveform table cell pin list, i.e. 'a0+a1+a2+clk'
    pins_to_remove = a list of pins, i.e. [ 'a0','clk']
    new_string = returned string 'a1+a2' '''
    a_cell = a_string.replace('\t','').replace('\n','').split('+')
    util._list_reduce(pins_to_remove,a_cell)
    return( '+'.join(a_cell) )
#select patterns for modification
class PatternModification:
    '''class wrapper for ModifyChannelData to handle batch processing of multiple patterns.
    Pass in signal header list, pins to remove (default is ""), pins to add (default is ""), and signal header name'''
    snap = time
    def __init__(self,pattern_file_list,destination_directory):
        if type(pattern_file_list) == type(''): self.pattern_file_list = [pattern_file_list]
        else: self.pattern_file_list = pattern_file_list
        self.destination_directory = destination_directory
    def modify_patterns(self,sig_header,pins_to_remove='', pins_to_add='', sig_header_name='', insert_before='',default_alias='X', format_list=''):
        '''
        sig_header: current signal header of patterns in pattern_file_list
        pins_to_remove: list of pins to pull out of signal header and pattern
        pins_to_add: list of pins to put into signal header, the default is to append it to the signal header
        sig_header_name: new signal header name for DefaultSignalHeader field in pattern, defaults to ''
        '''
        if type(pins_to_remove) == type('') and len(pins_to_remove)>0: pins_to_remove = [pins_to_remove]
        if type(pins_to_add) == type('') and len(pins_to_add)>0: pins_to_add = [pins_to_add]
        if type(format_list) == type('') and len(format_list)>0: format_list = [format_list]
        new_alias = '.'
        if len(default_alias)>0:
            new_alias = default_alias
        insert_here, AppendAtEnd = '',True
        if len(insert_before)>0:
            insert_here, AppendAtEnd = insert_before, False
        for pattern_file in self.pattern_file_list:
            a = self.snap()
            self.pat_in = util.FileUtils(pattern_file)
            self.pat_in.read_from_file()
            self.local_sig_header = copy.deepcopy(sig_header)
            self.pat_modify = ModifyChannelData(self.local_sig_header,self.pat_in.contents)
            if len(pins_to_remove) > 0: self.pat_modify.remove_pin(pins_to_remove)
            if len(pins_to_add) > 0: 
                self.pat_modify.add_pin(pins_to_add,append_at_the_end=AppendAtEnd,insert_before_pin=insert_here,default_alias=new_alias)
            if len(format_list) > 0: self.pat_modify.pretty_format(format_list)
            if sig_header_name != '': self.pat_modify._change_signal_header_name(sig_header_name)
            self.pat_out = util.FileUtils(self.destination_directory+'/'+self.pat_in.file)
            self.pat_out.write_to_file(self.pat_modify.all_lines)
            print "%s pattern modification complete, took %g seconds..."%(self.pat_out.file, self.snap()-a)
#modify patterns
class ModifyChannelData:
    '''Modify Pin Attribute in pattern vector: (signal_header, vector_list)
    change_alias: pass in dictionary { 'PinName': ('old_aliases', 'new_aliases'),...}
    remove_pin: pass in list of pins to remove from vector, signal header is modified accordingly 
    change_field: pass in field name, such as DefaultSignalHeader, and new field name
    add_pin: pass in list of pins to add to pattern vectors, signal header is modified accordingly.
             see ModifyChannelData.add_pin.__doc__ for more detail.
    shuffle_signal_header: pass in a new_signal header and remap vector line aliases to new pin sequence
    _change_signal_header_name: change signal header name for DefaultSignalHeader field in pattern
    translate_all_channel_data: remap aliases, say from IMAGE convention to TI, i.e. "01LHX-M" -> "LH01M-Z"
    pretty_format: add spacer after each pin passed in from pin_list in each vector of channel data
    '''
    def __init__(self, signal_header, all_lines):
        self.signal_header = signal_header
        self.sig_hdr_dict = dict([ (v,i) for i,v in enumerate(self.signal_header) ])
        self.all_lines = all_lines
        self.c = util.CaptureBlocks(all_lines)
        self.vector_list = all_lines[self.c.start_pts[0]:self.c.end_pts[0]]
        self.g = util.m_grep(self.vector_list)
        self.g.grep('\*([\w\.\-\_\s\%,]+)\*.*;.*') 
        self.vector_indices = [ int(float(i))-1 for i in self.g.coordinates ]
    def _change_signal_header_name(self,sig_header):
        g = util.m_grep(self.all_lines)
        g.grep('Default\s+SignalHeader\s+\w+;')
        if g.pattern_count == 1:
            index = int(float(g.coordinates[0]))-1
            Null = self.all_lines.pop(index)
            self.all_lines.insert(index,'Default SignalHeader '+sig_header+';\n')
    def translate_all_channel_data(self, old_aliases='01LHX-M', new_aliases='LH01M-Z'):
        '''convert aliases from IMAGE convention to TI convention'''
        self.translate_channels = TranslateAliases(old_aliases,new_aliases)
        for i in self.vector_indices:
            vector_line = ''.join(list(self.vector_list[i].split('*')[1].replace(' ','').replace('\t','')))
            vector_line = self.translate_channels.do_translation(vector_line)
            self.vector_list[i] = self.vector_list[i].split('*')[0]+'*'+vector_line+'*'+'*'.join(self.vector_list[i].split('*')[2:])
        self.all_lines[self.c.start_pts[0]:self.c.end_pts[0]] = self.vector_list
    def change_alias(self, aDict):
        '''aDict { 'PinName': ('old_aliases', 'new_aliases'), .... }'''
        aRange = range(len(self.vector_list))
        for aPin in aDict:
            trans_table = string.maketrans(aDict[aPin][0],aDict[aPin][1])
            pin_index = self.sig_hdr_dict[aPin]
            for i in aRange:
                if i in self.vector_indices:
                    vector_line = list(self.vector_list[i].split('*')[1].replace(' ','').replace('\t',''))
                    alias_value = vector_line.pop(pin_index)
                    #how to reinsert after alias swap?....
                    alias_value = alias_value.translate(trans_table)
                    vector_line.insert(pin_index,alias_value)
                    self.vector_list[i] = self.vector_list[i].split('*')[0]+'*'+''.join(vector_line)+'*'+'*'.join(self.vector_list[i].split('*')[2:])
        self.all_lines[self.c.start_pts[0]:self.c.end_pts[0]] = self.vector_list
    def remove_pin(self,pin_list):
        '''pass in list of pins to removed from vector'''        
        if type(pin_list) != type([]): pin_list = [pin_list]
        pin_indices = [ self.sig_hdr_dict[aPin] for aPin in pin_list ]
        pin_indices.sort()
        util.my_sort(pin_indices,-1) #sort and reverse
        for pin_index in pin_indices: self.signal_header.pop(pin_index)
        for aPin in pin_list: self.sig_hdr_dict.pop(aPin)
        for i in self.vector_indices:
            #pull out vector line and remove spaces between alias characters
            vector_line = list(self.vector_list[i].split('*')[1].replace(' ','').replace('\t',''))
            for pin_index in pin_indices: 
                try:
                    vector_line.pop(pin_index)
                except IndexError:
                    print 'pop index, %d, out of range for line %d:\n%s'%(pin_index,i,self.vector_list[i])
                    raise
            self.vector_list[i] = self.vector_list[i].split('*')[0]+'*'+''.join(vector_line)+'*'+'*'.join(self.vector_list[i].split('*')[2:])
        self.all_lines[self.c.start_pts[0]:self.c.end_pts[0]] = self.vector_list
        self.sig_hdr_dict = dict([ (v,i) for i,v in enumerate(self.signal_header) ])
    def add_pin(self,pins_to_add, append_at_the_end=True, insert_before_pin='', default_alias='.'):
        '''pass in a list of pins to add to pattern, append_at_the_end=True and insert_before_pin='' are default.  
        As is '.' for default_alias '''
        if type(pins_to_add) == type("string"): pins_to_add = [pins_to_add]
        if append_at_the_end: self.signal_header = self.signal_header + pins_to_add
        else: 
            aRange = range(len(pins_to_add))
            aRange.reverse()
            insert_here = self.signal_header.index(insert_before_pin)
            for index in aRange:
                self.signal_header.insert(insert_here,pins_to_add[index])
        for i in self.vector_indices:
            #pull out vector line and remove spaces between alias characters
            vector_line = list(self.vector_list[i].split('*')[1].replace(' ','').replace('\t',''))
            if append_at_the_end: vector_line.append(default_alias*len(pins_to_add))
            else: vector_line.insert(self.sig_hdr_dict[insert_before_pin],default_alias*len(pins_to_add))
            self.vector_list[i] = self.vector_list[i].split('*')[0]+'*'+''.join(vector_line)+'*'+'*'.join(self.vector_list[i].split('*')[2:])
        self.all_lines[self.c.start_pts[0]:self.c.end_pts[0]] = self.vector_list
        self.sig_hdr_dict = dict([ (v,i) for i,v in enumerate(self.signal_header) ])
    def shuffle_signal_header(self,new_signal_header):
        self.pin_sequence = [ util.find_index(new_signal_header,'^'+aPin+'$') for aPin in self.signal_header ]
        for i in self.vector_indices:
            #pull out vector line and remove spaces between alias characters
            vector_line = self.vector_list[i].split('*')[1].replace(' ','').replace('\t','')
            self.s = util.Scramble(vector_line, self.pin_sequence)
            self.vector_list[i] = self.vector_list[i].split('*')[0]+'*'+''.join(self.s.scrambled)+'*'+'*'.join(self.vector_list[i].split('*')[2:])
        self.signal_header = new_signal_header
        self.all_lines[self.c.start_pts[0]:self.c.end_pts[0]] = self.vector_list
        self.sig_hdr_dict = dict([ (v,i) for i,v in enumerate(self.signal_header) ])
    def pretty_format(self,pin_list):
        '''add spacer after each pin passed in from pin_list in each vector of channel data'''
        self.pin_sequence = [ util.find_index(self.signal_header,'^'+aPin+'$') for aPin in pin_list ]
        self.pin_sequence.reverse()
        for i in self.vector_indices:
            vector_line = list(self.vector_list[i].split('*')[1].replace(' ','').replace('\t','') )
            for j in self.pin_sequence: vector_line.insert(j+1,' ')
            self.vector_list[i] = self.vector_list[i].split('*')[0]+'*'+''.join(vector_line)+'*'+'*'.join(self.vector_list[i].split('*')[2:])
        self.all_lines[self.c.start_pts[0]:self.c.end_pts[0]] = self.vector_list
class MakePatternMap(enV.GenPatternMap):
#    def __init__(self, PatternMapName,DefaultSourcePath=None,DefaultBinaryPath=None,DefaultPatternGroup=None):
#{pattern_name: [filename_list, pathname_list=None, cachepath_list=None, groupname=None, evRemove=False] }
#pattern_dict = dict( [ (pattern_name.split('/')[-1].split('.')[0],[ pattern_name.split('/')[-1].split('.')[0],\
#            pattern_name.split('/')[-1],None,None,None,False]) for pattern_name in pattern_list] )
#    enum_dict = dict([ (v,i) for i,v in enumerate(['pattern_name','filename_list','pathname_list','cachepath_list','groupname','evRemove']) ]    
    def populate_pattern_map(self,pattern_list_dict):
        for aKey in pattern_list_dict.keys():
            pat_name,files,paths,cachepath,groupname,evRemove = pattern_list_dict[aKey]
            self.gen_pattern_entry(pat_name,files,paths,cachepath,groupname,evRemove) 
class TranslateAliases:
    def __init__(self,input_codes,output_codes):
        self.input_codes = input_codes
        self.output_codes = output_codes
        self.trans_table = string.maketrans(self.input_codes,self.output_codes)
    def do_translation(self,channel_data):
        self.channel_data = channel_data
        if type(channel_data) == type('a_string'):
            self.channel_data = self.channel_data.translate(self.trans_table)
        else:    
            for line in self.channel_data:
                line = line.translate(self.trans_table)
        return(self.channel_data)

