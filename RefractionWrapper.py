import subprocess
import multiprocessing as mp
from datetime import datetime
import struct
import time
import os
import errno
import shutil
import socket
import math
try:
    from tkinter import *
    from tkinter import messagebox, filedialog
except:
    from Tkinter import *
    from tkFileDialog import askdirectory
    from tkFileDialog import askopenfilename
    import tkMessageBox as messagebox
osgeo = False

title = "Refraction Wrapper"
version = "0.3"
master_path = r"\\cvo-isi-data.prodna.quantumspatial.com\nas"

def gui():

    main_frame = Tk()
    main_frame.resizable(width=TRUE, height=FALSE)
    main_frame.minsize(width=500, height=0)
    main_frame.title(title + " v" + version)
    try:
        main_frame.iconbitmap(os.path.join(master_path,
         'Programs\!QSI_Developed\Lara_Heitmeyer\Refraction_Wrapper\support_files\dark_side_of_rfx.ico'))
    except:
        pass

    # style parameters
    default_font = 'TkDefaultFont'
    optional_font = 'helvetica 8 italic'
    small_font = 'helvetica 6'
    default_color = '#a9a9a9'
    greyed_out = '#808080'

    # variables
    minimum_time_gap = StringVar()
    minimum_time_gap.set('20') #seconds
    concavity = StringVar()
    concavity.set('50') #m
    sensor_list = ["SN2354", "SN2846", "SN3976", "SN3977", "SN3978"]
    surfaces = ["grn", "nir", "upland"]
    ws_list = [surfaces[1]]
    settings_contents = []
    run_start_time = StringVar()
    ws_dict = {}
    shp_dict = {surfaces[0]: '', surfaces[1]: '', surfaces[2]: ''}
    steps = [("OBJ", 2), ("RFX", 3) , ("BIN", 4), (".mac", 5), ("GPL", 6), ("QC", 7), ("TIL", 8)]
    riegl_str_dict = {'grn': 'channel_g', 'ch0': 'channel_g_0', 'ch1': 'channel_g_1', 'nir': 'channel_ir',
                         'upland': 'upland'}
    attenuation_coeff_dict = {'SN3978': '0.975'}
    int_norm_dict = {'SN3978': ['-4200.00', '-2100.00']}

    # trace/clear functions
    def trj_override_hint_clearer(trj_override_entry):
        if trj_override_entry.get() == "trj start # override":
            trj_override_entry.delete(0, END)
            trj_override_entry.config(fg='black',  justify=CENTER)

    def swath_filter_hint_clearer(swath_filter_entry):
        if swath_filter_entry.get() == swath_filter_hint_txt:
            swath_filter_entry.delete(0, END)
            swath_filter_entry.config(fg='black', font=default_font, justify=CENTER)

    def ws_list_maker(*args):
        ws_list = []
        for surface in surfaces:
            if ws_dict[surface].var.get():
                ws_list.append(surface)
        return(ws_list)

    def start_end_validator(*args):
        start = int(processing_start.get())
        end = int(processing_end.get())
        for button in b_start:
            index = b_start.index(button) + 2 # hack since the original first 2 proc steps were removed
            if index > end:
                button.config(state=DISABLED)
            if index <= end:
                button.config(state=NORMAL)
        for button in b_end:
            index = b_end.index(button) + 2 # hack since the original first 2 proc steps were removed
            if index < start:
                button.config(state=DISABLED)
            if index >= start:
                button.config(state=NORMAL)

    def settings_file_reader(*args):
        if os.path.isfile(settings_file.get()):
            settings_contents = []
            with open(settings_file.get(), 'r') as settings:
                for line in settings:
                    settings_contents.append(line)
            def get_setting(setting_tag):
                for line in settings_contents:
                    setting = re.search(setting_tag + ': ([\s\S]*)' , line)
                    if setting:
                        return setting.group(1).strip()
            try:
                all_trj_dir.set(get_setting("Project Trajectories Folder"))
                deltek_id.set(get_setting("Project Deltek ID"))
                project_name.set(get_setting("Project Name"))
                tscan_project_template.set(get_setting("Terra PRJ Template"))
                tieline_settings_file.set(get_setting("Terra Tieline Settings File"))
                terra_transform_file.set(get_setting("Terra Transform File"))
                terra_ptc_file.set(get_setting("Terra PTC File"))
                gpl_macro_template.set(get_setting("Terra GPL Macro Template"))
                extract = get_setting("Default Extraction Location")
                if not extract:
                    extract = get_setting("Project Default IC Folder Location")
                if extract:
                    extract_entry.delete(0, END)
                    extract_entry.insert(END, extract)
                serial = get_setting("Default Sensor")
                if serial:
                    n = sensor_list.index(serial)
                    sensor.set(sensor_list[n])
                ws = get_setting("Default WS Sources")
                if ws:
                    ws_list = []
                    for surface in surfaces:
                        ws_dict[surface].var.set(False)
                        if surface in ws:
                            ws_list.append(surface)
                            ws_dict[surfaces[surfaces.index(surface)]].var.set(True)
                spd = get_setting("Speed")
                if spd:
                    speed.set(spd)
                    # speed_entry.delete(0, END)
                    # speed_entry.insert(END, speed)
                else:
                    speed.set('140')
                planned_height = get_setting("AGL")
                if planned_height:
                    agl.set(planned_height)
                    # speed_entry.delete(0, END)
                    # speed_entry.insert(END, speed)
                else:
                    agl.set('400')
                trj_buffer = get_setting("TRJ Buffer")
                if trj_buffer:
                    trj_buffer_size.set(trj_buffer)
                    # trj_buffer_entry.delete(0, END)
                    # trj_buffer_entry.insert(END, trj_buffer)
                else:
                    trj_buffer_size.set('1')
                spool = get_setting("Spool Up Time")
                if spool:
                    spool_up_time.set(spool)
                    # spool_entry.delete(0, END)
                    # spool_entry.insert(END, spool)
                else:
                    spool_up_time.set('0')
                clip = get_setting("Tail Clip")
                if clip:
                    tail_clip.set(clip)
                    # tail_clip_entry.delete(0, END)
                    # tail_clip_entry.insert(END, clip)
                else:
                    tail_clip.set('0')
                gap = get_setting("Minimum Time Gap")
                if gap:
                    minimum_time_gap.set(gap)
                con = get_setting("Concavity")
                if con:
                    concavity.set(con)
                email = get_setting("Default Username")
                if not email:
                    email = get_setting("Default Email")
                if email:
                    email_entry.delete(0, END)
                    email_entry.insert(END, email)
                # ws_req = get_setting("Project Default WS Required")
                # if ws_req:
                #     if ws_req == "True" or ws_req == "TRUE":
                #         ws_required.set(1)
                folder = get_setting("Mission Folder")
                if folder:
                    extract_entry.delete(0, END)
                    extract_entry.insert(END,folder)
                sn = get_setting("Sensor")
                if serial:
                    i=sensor_list.index(sn)
                    sensor.set(sensor_list[i])
                user = get_setting("Username")
                if user:
                    email_entry.delete(0, END)
                    email_entry.insert(END, email)
                s = get_setting("Surfaces")
                if s:
                    ws_list = []
                    for surface in surfaces:
                        ws_dict[surface].var.set(False)
                        if surface in s:
                            ws_list.append(surface)
                            ws_dict[surfaces[surfaces.index(surface)]].var.set(True)
                filter = get_setting("Swath Filter")
                if filter:
                    swath_filter_entry.delete(0, END)
                    swath_filter_entry.insert(END,filter)
                g = get_setting("Green Shapefile")
                if g:
                    shp_dict[surfaces[0]] = g
                    grn_shp.set(g)
                n = get_setting("NIR Shapefile")
                if n:
                    shp_dict[surfaces[1]] = n
                    nir_shp.set(n)
                u = get_setting("Upland Shapefile")
                if u:
                    shp_dict[surfaces[2]] = u
                    ul_shp.set(u)
                intermediate = get_setting("Intermediate QC").lower()
                if intermediate:
                    if intermediate == "true" or intermediate == "yes" or intermediate == "y":
                        optional_qc.set(1)
                    if intermediate == "false" or intermediate == "no" or intermediate == "n":
                        optional_qc.set(0)
                start = get_setting("Start Step")
                if start:
                    if start == "0" or start.lower() == "trj":
                        processing_start.set(0)
                    elif start == "1" or start.lower() == "lm1":
                        processing_start.set(1)
                    elif start == "2" or start.lower() == "obj":
                        processing_start.set(2)
                    elif start == "3" or start.lower() == "lm2" or start.lower() == "rfx":
                        processing_start.set(3)
                    elif start == "4" or start.lower() == "bin":
                        processing_start.set(4)
                    elif start == "5" or start.lower() == "mac" or start.lower() == ".mac":
                        processing_start.set(5)
                    elif start == "6" or start.lower() == "gpl":
                        processing_start.set(6)
                    elif start == "7" or start.lower() == "qc":
                        processing_start.set(7)
                    elif start == "7" or start.lower() == "til":
                        processing_start.set(8)
                end = get_setting("End Step")
                if end:
                    if end == "0" or end.lower() == "trj":
                        processing_end.set(0)
                    elif end == "1" or end.lower() == "lm1":
                        processing_end.set(1)
                    elif end == "2" or end.lower() == "obj":
                        processing_end.set(2)
                    elif end == "3" or end.lower() == "lm2" or end.lower() == "rfx":
                        processing_end.set(3)
                    elif end == "4" or end.lower() == "bin":
                        processing_end.set(4)
                    elif end == "5" or end.lower() == "mac" or end.lower() == ".mac":
                        processing_end.set(5)
                    elif end == "6" or end.lower() == "gpl":
                        processing_end.set(6)
                    elif end == "7" or end.lower() == "qc":
                        processing_end.set(7)
                    elif end == "7" or end.lower() == "til":
                        processing_end.set(8)
                instances = get_setting("Instances")
                if instances:
                    if int(instances) in range(1,33):
                        threads.set(instances)
            except Exception as e:
                ok = messagebox.askokcancel("Warning",
                                            "Unable to read all expected parameters from settings file.\n"
                                            "Please verify settings filepath and contents.\n"
                                            "Error details: %s\n"
                                            "Continue?" % e)
                if ok:
                    pass
                else:
                    mainloop_wrapper(main_frame)
        start_button_enable()

    def settings_file_writer():
        run_start_time = (datetime.now().strftime('%y%m%d_%H%M%S'))
        input_settings_file_contents = []
        settings_contents = []
        with open(settings_file.get()) as set:
            for line in set:
                input_settings_file_contents.append(line)
        for line in input_settings_file_contents:
            if '-' * 60 + ' RUN' in line:
                break
            else:
                settings_contents.append(line)
        settings_contents.append('-' * 60 + ' RUN ' + run_start_time + ' ' + '-' * 60 + '\n')
        settings_contents.append('\n')
        settings_contents.append('Mission Folder: %s\n' % IC_folder.get())
        settings_contents.append('Sensor: %s\n' % sensor.get())
        settings_contents.append('Username: %s\n' % email.get())
        ws_list = ws_list_maker()
        ws_string = ''
        ws_string = " ".join(s for s in ws_list)
        settings_contents.append('Surfaces: %s \n' % ws_string)
        settings_contents.append('Swath Filter: %s\n' % swath_filter.get())
        settings_contents.append('Green Shapefile: %s\n' % shp_dict[surfaces[0]])
        settings_contents.append('NIR Shapefile: %s\n' % shp_dict[surfaces[1]])
        settings_contents.append('Upland Shapefile: %s\n' % shp_dict[surfaces[2]])
        settings_contents.append('Intermediate QC: %s\n' % bool(optional_qc.get()))
        ss = ''
        es = ''
        for name, step in steps:
            if step == int(processing_start.get()):
                ss = name
            if step == int(processing_end.get()):
                es = name
        settings_contents.append('Start Step: %s\n' % ss)
        settings_contents.append('End Step: %s\n' % es)
        settings_contents.append('Instances: %s\n' % threads.get())
        return(run_start_time, settings_contents)

    def start_button_enable(*args):
        if int(processing_start.get()) > 3:
            for surface in surfaces:
                ws_dict[surface].config(state=DISABLED)
            swath_filter_entry.config(state=DISABLED)
            nir_shp_frame.pack_forget()
            grn_shp_frame.pack_forget()
            ul_shp_frame.pack_forget()
            shp_spc.pack()
            ws_shp_frame.pack(fill=X, expand=1)
            ws_list = []
        else:
            for surface in surfaces:
                ws_dict[surface].config(state=NORMAL)
            swath_filter_entry.config(state=NORMAL)
            shp_spc.pack_forget()
            nir_shp_frame.pack_forget()
            grn_shp_frame.pack_forget()
            ul_shp_frame.pack_forget()
            ws_list = []
            ws_shp_frame.pack(fill=X, expand=1)
            if ws_dict[surfaces[0]].var.get():
                grn_shp_frame.pack(fill=X, expand=1)
                ws_list.append(surfaces[0])
                shp_dict[surfaces[0]] = grn_shp.get()
            if ws_dict[surfaces[1]].var.get():
                nir_shp_frame.pack(fill=X, expand=1)
                ws_list.append(surfaces[1])
                shp_dict[surfaces[1]] = nir_shp.get()
            if ws_dict[surfaces[2]].var.get():
                ul_shp_frame.pack(fill=X, expand=1)
                ws_list.append(surfaces[2])
                shp_dict[surfaces[2]] = ul_shp.get()
            if '"' in shp_dict[surfaces[0]]:
                g = grn_shp.get().replace('"', '')
                grn_shp.set(g)
                grn_shp_entry.delete(0, END)
                grn_shp_entry.insert(END, g)
                start_button_enable()
            if '"' in shp_dict[surfaces[1]]:
                n = nir_shp.get().replace('"', '')
                nir_shp.set(n)
                nir_shp_entry.delete(0, END)
                nir_shp_entry.insert(END, n)
                start_button_enable()
            if '"' in shp_dict[surfaces[2]]:
                u = ul_shp.get().replace('"', '')
                ul_shp.set(u)
                ul_shp_entry.delete(0, END)
                ul_shp_entry.insert(END, u)
                start_button_enable()

        qc_frame.pack_forget()
        if int(processing_start.get()) < 4:
            if int(processing_end.get()) < 3:
                pass
            else:
                qc_frame.pack(fill=X, expand=1)

        if swath_filter_entry.get() == '':
            swath_filter_entry.delete(0, END)
            swath_filter_entry.insert(END, swath_filter_hint_txt)
            swath_filter_entry.config(fg=default_color, font=optional_font, justify=CENTER)

        if '"' in settings_file.get():
            f = settings_file.get().replace('"', '')
            settings_entry.delete(0, END)
            settings_entry.insert(END, f)
            settings_file_reader()

        if os.path.isfile(settings_file.get()) or settings_file.get() == '':
            settings_entry.config(bg='white')
        else:
            settings_entry.config(bg='firebrick1')

        shps_valid = True
        if surfaces[0] in ws_list:
            if os.path.isfile(shp_dict[surfaces[0]]) and shp_dict[surfaces[0]].endswith('.shp'):
                grn_shp_entry.config(bg='white')
            elif shp_dict[surfaces[0]] == '':
                shps_valid = False
                nir_shp_entry.config(bg='white')
            else:
                shps_valid = False
                grn_shp_entry.config(bg='firebrick1')
        if surfaces[1] in ws_list:
            if os.path.isfile(shp_dict[surfaces[1]]) and shp_dict[surfaces[1]].endswith('.shp'):
                nir_shp_entry.config(bg='white')
            elif shp_dict[surfaces[1]] == '':
                shps_valid = False
                nir_shp_entry.config(bg='white')
            else:
                shps_valid = False
                nir_shp_entry.config(bg='firebrick1')
        if surfaces[2] in ws_list:
            if os.path.isfile(shp_dict[surfaces[2]]) and shp_dict[surfaces[2]].endswith('.shp'):
                ul_shp_entry.config(bg='white')
            elif shp_dict[surfaces[2]] == '':
                shps_valid = False
                nir_shp_entry.config(bg='white')
            else:
                shps_valid = False
                ul_shp_entry.config(bg='firebrick1')

        if os.path.isdir(IC_folder.get()):
            extract_entry.config(bg='white')
            if len(ws_list) == 0:
                if int(processing_start.get()) > 3:
                    start_button.config(state=NORMAL)
                else:
                    start_button.config(state=DISABLED)
            else:
                if shps_valid:
                    start_button.config(state=NORMAL)
                else:
                    start_button.config(state=DISABLED)
        elif IC_folder.get() == '':
            start_button.config(state=DISABLED)
            extract_entry.config(bg='white')
        else:
            start_button.config(state=DISABLED)
            extract_entry.config(bg='firebrick1')

    # entry section
    IC_folder = StringVar()
    extract_entry_frame = Frame(main_frame)
    extract_entry_frame.pack(fill=X, expand=1, pady=2)
    Label(extract_entry_frame, text="mission folder:", width=12, anchor=E).pack(side=LEFT)
    extract_entry = Entry(extract_entry_frame, textvariable=IC_folder, width=51)
    extract_entry.pack(side=LEFT, padx=1, fill=X, expand=1)
    Button(extract_entry_frame, text=' ... ', command=lambda: browser('Folder', extract_entry, 'folder')).pack(side=LEFT, padx=2)
    
    # calibration_location = StringVar()
    # calib_entry_frame = Frame(main_frame)
    # calib_entry_frame.pack(fill=X, expand=1, pady=2)
    # Label(calib_entry_frame,text="calib location:", width=12, anchor=E).pack(side=LEFT)
    # calib_entry = Entry(calib_entry_frame, textvariable=calibration_location, width=51)
    # calib_entry.pack(side=LEFT, padx=1, fill=X, expand=1)
    # Button(calib_entry_frame, text=' ... ', command=lambda: browser('Folder', calib_entry)).pack(side=LEFT, padx=2)
    #calib_entry.insert(END, r'Z:\2018_FL_NOAA_FloridaKeys_R032865\05_Calibration\00_mission_proc')

    settings_file = StringVar()
    settings_entry_frame = Frame(main_frame)
    settings_entry_frame.pack(fill=X, expand=1, pady=2)
    Label(settings_entry_frame,text="settings file:", width=12, anchor=E).pack(side=LEFT)
    settings_entry = Entry(settings_entry_frame, textvariable=settings_file, width=51)
    settings_entry.pack(side=LEFT, padx=1, fill=X, expand=1)
    Button(settings_entry_frame, text=' ... ', command=lambda: browser('File', settings_entry, 'settings')).pack(side=LEFT, padx=2)
    install_dir = os.getcwd()
    install_files = os.listdir(install_dir)
    settings_path = ''
    for item in install_files:
        if '.settings' in item:
            settings_path = os.path.join(install_dir, item)
    #settings_path = r"Y:\2018_Regional_ChesapeakeBayOption1_R031060\05_Calibration\00_Resources\temp.settings"
    settings_entry.insert(END, settings_path)

    sensor = StringVar()
    sensor.set(sensor_list[0])
    mission_info_frame = Frame(main_frame)
    mission_info_frame.pack(fill=X, expand=1, pady=2)
    Label(mission_info_frame, text="sensor:", width=12, anchor=E).pack(side=LEFT)
    sensor_entry = OptionMenu(mission_info_frame, sensor, *sensor_list)
    #sensor_entry = Entry(mission_info_frame, textvariable=sensor, width=7)
    sensor_entry.pack(side=LEFT)
    #sensor_entry.insert(END, "SN")
    # Label(mission_info_frame, text="agl(m):", width=14, anchor=E).pack(side=LEFT)
    # agl_entry = Entry(mission_info_frame, textvariable=agl, width=4)
    # agl_entry.pack(side=LEFT, padx=1)
    # agl_entry.insert(END, "400")
    Label(mission_info_frame, text="", fg=default_color, anchor=E, width=14).pack(side=LEFT)
    email = StringVar()
    #Label(mission_info_frame, text="email:", width=7, anchor=E).pack(side=LEFT)
    email_entry = Entry(mission_info_frame, textvariable=email, width=10, justify=RIGHT)
    email_entry.pack(side=LEFT, fill=X, expand=1)
    Label(mission_info_frame, text="@quantumspatial.com", width=17, anchor=E).pack(side=LEFT)
    Label(mission_info_frame, text="", width=3, anchor=E).pack(side=LEFT, padx=1)

    # trj_override_entry = Entry(mission_info_frame, textvariable=trj_start_override, width=25,
    #                            fg=default_color, font=optional_font, justify=CENTER)
    # trj_override_entry.pack(side=LEFT, padx=1)
    # trj_override_entry.insert(END, "trj start # override")
    # trj_override_entry.bind("<Button-1>", lambda event: trj_override_hint_clearer(trj_override_entry))
    # Label(mission_info_frame, text="", width=3, anchor=E).pack(side=LEFT, padx=1)

    flying_height = StringVar()
    speed = StringVar()
    agl = StringVar()
    trj_buffer_size = StringVar()
    tail_clip = StringVar()
    spool_up_time = StringVar()
    flying_height.set('400')
    speed.set('140')
    ###FIXME agl v flying height
    agl.set('400')
    trj_buffer_size.set('1')
    tail_clip.set('0')
    spool_up_time.set('0')
    # trj_info_frame = Frame(main_frame)
    # trj_info_frame.pack(fill=X, expand=1, pady=2)
    # Label(trj_info_frame, text="speed(kn):", width=12, anchor=E).pack(side=LEFT)
    # speed_entry = Entry(trj_info_frame, textvariable=speed, width=3)
    # speed_entry.pack(side=LEFT, padx=1)
    # #speed_entry.insert(END, "140")
    # Label(trj_info_frame, text="traj buff(s):", width=11, anchor=E).pack(side=LEFT)
    # trj_buffer_entry = Entry(trj_info_frame, textvariable=trj_buffer_size, width=2)
    # trj_buffer_entry.pack(side=LEFT, padx=1)
    # #trj_buffer_entry.insert(END, "1")
    # Label(trj_info_frame, text="tail clip(m):", width=11, anchor=E).pack(side=LEFT)
    # tail_clip_entry = Entry(trj_info_frame, textvariable=tail_clip, width=4)
    # tail_clip_entry.pack(side=LEFT, padx=1)
    # #tail_clip_entry.insert(END, "225")
    # Label(trj_info_frame, text="spool up(s):", anchor=E).pack(side=LEFT, fill=X, expand=1)
    # spool_entry = Entry(trj_info_frame, textvariable=spool_up_time, width=4)
    # spool_entry.pack(side=LEFT, padx=1)
    # #spool_entry.insert(END, "1.6") #(END, "9.5")
    # Label(trj_info_frame, text="", width=3, anchor=E).pack(side=LEFT, padx=1)
    # lmvars_entry_frame = Frame(main_frame)
    # lmvars_entry_frame.pack(fill=X, expand=1, pady=2)
    deltek_id = StringVar()
    project_name = StringVar()
    all_trj_dir = StringVar()
    green_ch0_las_monkey_config = StringVar()
    green_ch1_las_monkey_config = StringVar()
    nir_las_monkey_config = StringVar()
    rfx_las_monkey_config = StringVar()
    tscan_project_template = StringVar()
    tieline_settings_file = StringVar()
    terra_transform_file = StringVar()
    terra_ptc_file = StringVar()
    gpl_macro_template = StringVar()
    # Label(lmvars_entry_frame,text="project name:", width=12, fg=default_color, anchor=E).pack(side=LEFT)
    # proj_name_entry = Entry(lmvars_entry_frame, textvariable=project_name, fg=default_color)
    # proj_name_entry.pack(side=LEFT, fill=X, expand=1, padx=1)
    # proj_name_entry.insert(END, "Florida_Keys")
    # Label(lmvars_entry_frame, text="deltek id:", fg=default_color, width=8, anchor=E).pack(side=LEFT)
    # deltek_id_entry = Entry(lmvars_entry_frame, textvariable=deltek_id, width=9, fg=default_color)
    # deltek_id_entry.pack(side=LEFT, padx=1)
    # deltek_id_entry.insert(END, "032865.00")
    # Label(lmvars_entry_frame, text="", width=3, anchor=E).pack(side=LEFT, padx=1)

    misc_frame = Frame(main_frame)
    misc_frame.pack(fill=X, expand=1, pady=2)
    Label(misc_frame, text="surfaces:", width=12, anchor=E).pack(side=LEFT)

    # def upon_select(widget):
    #     print("%s is %s." % (widget['text'], widget.var.get()))

    for surface in surfaces:
        ws_dict[surface] = Checkbutton(misc_frame, text=surface, onvalue=True, offvalue=False)
        ws_dict[surface].var = BooleanVar()
        ws_dict[surface]['variable'] = ws_dict[surface].var
        #ws_dict[surface]['command'] = lambda w=ws_dict[surface]: upon_select(w)
        ws_dict[surface].pack(side=LEFT)
    ws_dict['nir'].select()

    swath_filter = StringVar()
    swath_filter_hint_txt = "swath filter list (e.g. 160003, 160734)"
    Label(misc_frame, text="", fg=default_color, anchor=E, width=4).pack(side=LEFT)
    swath_filter_entry = Entry(misc_frame, textvariable=swath_filter, width=30,
                               fg=default_color, font=optional_font, justify=CENTER)
    swath_filter_entry.pack(side=LEFT, fill=X, expand=1, padx=1)
    swath_filter_entry.insert(END, swath_filter_hint_txt)
    swath_filter_entry.bind("<Button-1>", lambda event: swath_filter_hint_clearer(swath_filter_entry))
    Label(misc_frame, text="", fg=default_color, anchor=E, width=3).pack(side=LEFT, padx=1)
    trj_start_override = StringVar()

    ws_shp_frame = Frame(main_frame)
    ws_shp_frame.pack(fill=X, expand=1)
    grn_shp_frame = Frame(ws_shp_frame)
    #grn_shp_frame.pack(fill=X, expand=1)
    nir_shp_frame = Frame(ws_shp_frame)
    nir_shp_frame.pack(fill=X, expand=1)
    ul_shp_frame = Frame(ws_shp_frame)
    #ul_shp_frame.pack(fill=X, expand=1)
    grn_shp = StringVar()
    nir_shp = StringVar()
    ul_shp = StringVar()
    shp_spc = Label(ws_shp_frame, text='', height=1)
    shp_spc.pack(side=LEFT)
    Label(grn_shp_frame, text="%s shp:" % surfaces[0], width=12, anchor=E).pack(side=LEFT)
    grn_shp_entry = Entry(grn_shp_frame, textvariable=grn_shp, width=51)
    grn_shp_entry.pack(side=LEFT, padx=1, fill=X, expand=1)
    Button(grn_shp_frame, text=' ... ', command=lambda: browser('File', grn_shp_entry, 'shape')).pack(side=LEFT, padx=2)
    Label(nir_shp_frame, text="%s shp:" % surfaces[1], width=12, anchor=E).pack(side=LEFT)
    nir_shp_entry = Entry(nir_shp_frame, textvariable=nir_shp, width=51)
    nir_shp_entry.pack(side=LEFT,padx=1, fill=X, expand=1)
    Button(nir_shp_frame, text=' ... ', command=lambda: browser('File', nir_shp_entry, 'shape')).pack(side=LEFT, padx=2)
    Label(ul_shp_frame, text="%s shp:" % surfaces[2], width=12, anchor=E).pack(side=LEFT)
    ul_shp_entry = Entry(ul_shp_frame, textvariable=ul_shp, width=51)
    ul_shp_entry.pack(side=LEFT, padx=1, fill=X, expand=1)
    Button(ul_shp_frame, text=' ... ', command=lambda: browser('File', ul_shp_entry, 'shape')).pack(side=LEFT, padx=2)
    grn_shp.set('')
    nir_shp.set('')
    ul_shp.set('')


    # check_frame = Frame(main_frame)
    # check_frame.pack(fill=X, expand=1)
    ws_required = IntVar()
    ws_required.set(0)
    # Checkbutton(check_frame, variable=ws_required, width=12, anchor=E).pack(side=LEFT)
    # Label(check_frame, text="require water surface for all swaths", anchor=N).pack(side=LEFT)
    qc_frame = Frame(ws_shp_frame)
    qc_frame.pack(fill=X, expand=1, padx=4)
    optional_qc = IntVar()
    optional_qc.set(1)
    Label(qc_frame, text="", width=12).pack(side=LEFT)
    Checkbutton(qc_frame, variable=optional_qc, text="output intermediate qc layers after refraction").pack(side=LEFT)


    go_frame = Frame(main_frame)
    go_frame.pack(pady=5)
    start_stop_frame = Frame(go_frame)
    start_stop_frame.pack(side=LEFT)
    start_frame = Frame(start_stop_frame)
    start_frame.pack()
    Label(start_frame, text="start step:", width=12, anchor=E).pack(side=LEFT)
    end_frame = Frame(start_stop_frame)
    end_frame.pack()
    Label(end_frame, text="end step:", width=12, anchor=E).pack(side=LEFT)
    processing_start = StringVar()
    processing_end = StringVar()
    b_start = []
    for text, number in steps:
        b = Radiobutton(start_frame, text=text, variable=processing_start, value=number, indicatoron=0, font=small_font)
        b.pack(side=LEFT)
        b_start.append(b)
    b_end = []
    for text, number in steps:
        b = Radiobutton(end_frame, text=text, variable=processing_end, value=number, indicatoron=0, font=small_font)
        b.pack(side=LEFT)
        b_end.append(b)
    processing_start.set(2)
    processing_end.set(7)

    Label(go_frame, text="", width=3, anchor=E).pack(side=LEFT, padx=1)
    Label(go_frame, text="instances:").pack(side=LEFT)
    threads = StringVar()
    machine_threads = mp.cpu_count()
    threads.set(machine_threads)
    threads_selector = Spinbox(go_frame, from_=1, to=32, textvariable=threads, width=2)
    threads_selector.pack(side=LEFT)

    Label(go_frame, text="", width=3, anchor=E).pack(side=LEFT, padx=1)
    start_button = Button(go_frame, text=' START ', font='helvetica 10 bold', state=DISABLED,
                          command=lambda: [swath_filter_hint_clearer(swath_filter_entry),
                                           validator(main_frame, IC_folder.get(),
                                                    email.get() + '@quantumspatial.com', deltek_id.get(),
                                                    project_name.get(), all_trj_dir.get(),
                                                    green_ch0_las_monkey_config.get(),
                                                    green_ch1_las_monkey_config.get(), nir_las_monkey_config.get(),
                                                    rfx_las_monkey_config.get(), tscan_project_template.get(),
                                                    tieline_settings_file.get(), terra_transform_file.get(),
                                                    terra_ptc_file.get(), gpl_macro_template.get(), ws_required.get(),
                                                    optional_qc.get(), agl.get(), sensor.get(),
                                                    int(trj_buffer_size.get()), int(tail_clip.get()),
                                                    trj_start_override.get(), float(spool_up_time.get()),
                                                    int(speed.get()), int(processing_start.get()),
                                                    int(processing_end.get()), threads.get(), surfaces, ws_list_maker(),
                                                    shp_dict, riegl_str_dict, attenuation_coeff_dict, int_norm_dict,
                                                    swath_filter.get(), minimum_time_gap.get(), concavity.get(),
                                                    settings_file_writer()[0], settings_file_writer()[1])])
    start_button.pack(side=LEFT, padx=5)

    # metavalidate version
    if not os.path.isdir(master_path):
        ok = messagebox.askokcancel("Warning",
                                      "Unable to connect to network storage location where this script is hosted\n"
                                      "(%s).\n Continue?" % master_path)
        if ok:
            pass
        else:
            exit(0)

    self_master_path = os.path.join(master_path, 'Programs\!QSI_Developed\Lara_Heitmeyer\Refraction_Wrapper\RefractionWrapper.py')
    if not os.path.isfile(self_master_path):
        ok = messagebox.askokcancel("Warning",
                                      "Unable to find master version of this script file on hosted network storage\n"
                                      "(%s).\n Continue?" % self_master_path)
        if ok:
            pass
        else:
            exit(0)

    try:
        version_info = ""
        with open(self_master_path, 'r') as script:
            for line in script:
                version_string = re.search('version = "(\S*)"\n', line)
                if version_string:
                    version_info = version_string.group(1)
                    break

        if not version_info == version:
                ok = messagebox.askokcancel("Warning",
                                              "There is a newer version of this script available.\n"
                                              "Unless intentionally running an older version, please cancel "
                                              "and run the script located at:\n %s\n\n"
                                              % self_master_path)
                if ok:
                    pass
                else:
                    exit(0)
    except:
        pass

    if os.path.isfile(settings_file.get()):
        settings_file_reader()

    processing_start.trace("w", start_end_validator)
    processing_end.trace("w", start_end_validator)
    settings_file.trace("w", settings_file_reader)
    IC_folder.trace("w", start_button_enable)
    #calibration_location.trace("w", start_button_enable)
    sensor.trace("w", start_button_enable)
    ws_dict[surfaces[0]].var.trace("w", start_button_enable)
    ws_dict[surfaces[1]].var.trace("w", start_button_enable)
    ws_dict[surfaces[2]].var.trace("w", start_button_enable)
    nir_shp.trace("w", start_button_enable)
    grn_shp.trace("w", start_button_enable)
    ul_shp.trace("w", start_button_enable)
    #ws_required.trace("w", start_button_enable)
    optional_qc.trace("w", start_button_enable)
    email.trace("w", start_button_enable)
    threads.trace("w", start_button_enable)
    processing_start.trace("w", start_button_enable)
    processing_end.trace("w", start_button_enable)

    main_frame.mainloop()


def validator(main_frame, IC_folder, email, deltek_id, project_name, all_trj_dir, green_ch0_las_monkey_config,
              green_ch1_las_monkey_config, nir_las_monkey_config, rfx_las_monkey_config,tscan_project_template,
              tieline_settings_file, terra_transform_file, terra_ptc_file, gpl_macro_template, ws_required, optional_qc,
              agl, sensor, trj_buffer_size, tail_clip, trj_start_override, spool_up_time, speed, processing_start,
              processing_end, threads, surfaces, ws_list, shp_dict, riegl_str_dict, attenuation_coeff_dict,
              int_norm_dict, swath_filter, minimum_time_gap, concavity, run_start_time, settings_contents):

    print('Please wait until input validation completes to ensure a successful run! Starting preprocessing ... ')

    ### TODO add a check comparing trj to las and check for short trj
    # define parameters folder structure & shared files
    grn_number_start = '10000'

    # define validate and format mission name
    mission_folder = IC_folder
    mission_name = os.path.basename(IC_folder)
    mission_string = re.search('([1-9][0-9][0-1][0-9][0-3][0-9])_(SN[0-9]{4})_F([0-9])', mission_name)
    if not mission_string:
        messagebox.showwarning('Input Error',
                               'Unexpected naming convention for mission folder.\n'
                               'Folder name must be \"YYMMDD_SN####_F#\"')
        mainloop_wrapper(main_frame)
    if not mission_string.group(2) == sensor:
        messagebox.showwarning('Input Error',
                               'Sensor number selected does not match sensor number in extract folder name.\n')
        mainloop_wrapper(main_frame)

    mission_date = datetime.strptime(mission_string.group(1), '%y%m%d').strftime('%m/%d/%y')

    mission_number = mission_string.group(3)
    ### deprecated: using LL for trj splitting
    #trj_folder = os.path.join(mission_folder, "3_Trajectories")
    trj_input_folder = '' #os.path.join(trj_folder, "1_traj_full")
    trj_output_folder = os.path.join(mission_folder, "03_SplitTRJ__LL")
    exported_folder = os.path.join(mission_folder, "02_SwathLAS__LL")
    ICer_folder = os.path.join(mission_folder, "08_Refraction")
    wsm_folder = os.path.join(ICer_folder,"00_WSM")
    monkeyed_folder = os.path.join(mission_folder, "05_SwathLASGnd__LL")#ICer_folder, "01_geoid_applied")
    ws_las_input_folder = os.path.join(ICer_folder, "05_ellipsoid_ws_swaths")
    ws_las_folder = os.path.join(wsm_folder, "3_final_ws_las")
    obj_folder = os.path.join(ICer_folder, "06_OBJs")
    rfx_folder = os.path.join(ICer_folder, "07_refracted")
    nir_folder = os.path.join(exported_folder, "ChIR")
    #grn_folder = os.path.join(exported_folder, "grn")
    ch0_folder = os.path.join(exported_folder, "ChG_0")
    ch1_folder = os.path.join(exported_folder, "ChG_1")
    # ch0_monkeyed_folder = os.path.join(monkeyed_folder, "ChG_0")
    # ch1_monkeyed_folder = os.path.join(monkeyed_folder, "ChG_1")
    # nir_monkeyed_folder = os.path.join(monkeyed_folder, "Ch_IR")
    #mission_calib_folder = os.path.join(mission_folder, "6_")
    reports_folder = os.path.join(wsm_folder, "__reports")
    calib_trj_folder = '' #os.path.join(reports_folder, "0_trajectories")
    import_folder = os.path.join(ICer_folder, "08_imported")
    gpl_folder = os.path.join(ICer_folder, "09_gpch")
    gpl_qc_folder = os.path.join(gpl_folder, "qc_%s" % run_start_time)
    tielines_folder = os.path.join(gpl_folder, "tielines")

    #folder_maker(mission_calib_folder, main_frame, "skip")
    folder_maker(reports_folder, main_frame, "skip")
    folder_maker(rfx_folder, main_frame, "skip")
    folder_maker(ws_las_folder, main_frame, "skip")

    temp_folder = os.path.join(reports_folder, '__temp_tslave_folder')
    tslave_progress_folder = os.path.join(temp_folder, "progress")
    tslave_reports_folder = os.path.join(temp_folder, "reports")
    tslave_task_folder = os.path.join(temp_folder, "task")

    import_project = os.path.join(reports_folder, "0_TSCAN_import.prj")
    imported_project = os.path.join(reports_folder, "0_TSCAN_imported.prj")
    gpl_project = os.path.join(reports_folder, "1_TSCAN_gpl.prj")
    macro_directory = os.path.split((os.path.abspath(gpl_macro_template)))[0]
    mission_gpl_macro = os.path.join(macro_directory, "NOAA_step1_" + mission_name + ".mac")

    ch0las_list = []
    ch1las_list = []
    nirlas_list = []

    #write settings file
    settings_file = os.path.join(reports_folder, "__Refraction_Wrapper__Run_%s.settings" % (run_start_time))
    print("... writing settings file %s ..." % settings_file)
    with open (settings_file, 'w') as f:
        for line in settings_contents:
            f.write(line)
    # create list of steps to be executed
    print("... checking inputs and dependencies ...")
    processing_steps = range((processing_end - processing_start) + 1)
    for n in range(len(processing_steps)):
        processing_steps[n] += processing_start

    # validate software dependencies
    las_monkey_folder = r"C:\install\Las Monkey"
    las_monkey_file_path = os.path.join(las_monkey_folder, "LasMonkey.exe")
    lastools_path = r"C:\install\LAStools\bin"
    lastools_version_txt = os.path.join(lastools_path, "lastoolslicense.txt")
    lastools_expected_version = "200223"
    terra_path = r"C:\terra64"

    if not os.path.isfile(las_monkey_file_path):
        messagebox.showwarning('Error',
                                 'LasMonkey.exe is not in the expected location (%s).' % las_monkey_folder)
        mainloop_wrapper(main_frame)

    if not os.path.isdir(lastools_path):
        messagebox.showwarning('Error',
                                 'LasTools is not installed in the expected location (%s).' % lastools_path)
        mainloop_wrapper(main_frame)

    try:
        with open(lastools_version_txt, 'r') as txt:
            lastools_version = txt.read()

        if lastools_expected_version not in lastools_version:

            ok = messagebox.askokcancel("Warning",
                                          "Expected LasTools version (%s) not found in "
                                          "(%s).\nContinue?" % (lastools_expected_version, lastools_path))
            if ok:
                pass
            else:
                mainloop_wrapper(main_frame)

    except IOError:
        ok = messagebox.askokcancel("Warning",
                                      "Unable to find version info in LasTools install at %s"
                                      ".\nContinue?" % lastools_version_txt)
        if ok:
            pass
        else:
            mainloop_wrapper(main_frame)

    if not os.path.isdir(terra_path):
        messagebox.showwarning('Error',
                                 'TerraSolid is not installed in the expected location (C:\\terra64).')
        mainloop_wrapper(main_frame)

    ### FIXME update these to actually test - move tmatch
    # if not os.path.isfile(os.path.join(terra_path, "license", "tscan.lic")):
    #     messagebox.showwarning('Error',
    #                              'TerraScan license is not checked out to local machine.')
    #     mainloop_wrapper(main_frame)
    #
    # if not os.path.isfile(os.path.join(terra_path, "license", "tmatch.lic")):
    #     messagebox.showwarning('Error',
    #                              'TerraMatch license is not checked out to local machine.')
    #     mainloop_wrapper(main_frame)


    trj_lock_file = os.path.join(all_trj_dir, "NOAA_IC_TRJLOCK.lock")

    if not os.path.isfile(tieline_settings_file):
        messagebox.showwarning('Error',
                                 'TerraMatch tieline settings file does not exist.')
        mainloop_wrapper(main_frame)

    if not os.path.isfile(tieline_settings_file):
        messagebox.showwarning('Error',
                                 'TerraScan PTC file does not exist.')
        mainloop_wrapper(main_frame)

    if not os.path.isfile(terra_transform_file):
        messagebox.showwarning('Error',
                                 'TerraScan transfomation definition file does not exist.')
        mainloop_wrapper(main_frame)

    if not os.path.isfile(tscan_project_template):
        messagebox.showwarning('Error',
                                 'TScan project template macro does not exist.')
        mainloop_wrapper(main_frame)

    if not os.path.isfile(gpl_macro_template):
        messagebox.showwarning('Error',
                                 'gpl template macro does not exist.')
        mainloop_wrapper(main_frame)

    if not os.path.isdir(all_trj_dir):
        messagebox.showwarning('Error',
                                 'Project trajectories directory does not exist.')
        mainloop_wrapper(main_frame)

    if not os.path.isdir(mission_folder):
        messagebox.showwarning('Input Error',
                                 'Mission folder on extract drive does not exist.')
        mainloop_wrapper(main_frame)

    folder_maker(ICer_folder, main_frame, "skip")
    folder_maker(ws_las_folder, main_frame, "skip")

    if processing_start < 2:

        if (1 or 0) in processing_steps:
            messagebox.showwarning('Error',
                                     'Trajectory splitting and LasMonkey swath prep are longer supported.\n'
                                     'Please use LidarLauncher to perform these steps,\n'
                                     'then choose a new processing start step, or switch to an older version.')
            mainloop_wrapper(main_frame)

        ch0las_count = 0
        for item in os.listdir(ch0_folder):
            if item.lower().endswith(".las"):
                ch0las_count += 1

        ch1las_count = 0
        for item in os.listdir(ch1_folder):
            if item.lower().endswith(".las"):
                ch1las_count += 1

        nirlas_count = 0
        for item in os.listdir(nir_folder):
            if item.lower().endswith(".las"):
                nirlas_count += 1

        if not os.path.isdir(exported_folder):
            messagebox.showwarning('Input Error',
                                     '2_Exported_Swaths folder does not exist in the mission folder on the extract drive.')
            mainloop_wrapper(main_frame)

        if not os.path.isdir(nir_folder):
            messagebox.showwarning('Input Error',
                                     'nir folder does not exist in 2_Exported_Swaths folder on the extract drive.')
            mainloop_wrapper(main_frame)

        if not os.path.isdir(ch0_folder):
            messagebox.showwarning('Input Error',
                                     'ch0 folder does not exist in 2_Exported_Swaths\grn folder on the extract drive.')
            mainloop_wrapper(main_frame)

        if not os.path.isdir(ch1_folder):
            messagebox.showwarning('Input Error',
                                     'ch1 folder does not exist in 2_Exported_Swaths\grn folder on the extract drive.')
            mainloop_wrapper(main_frame)

        if not os.path.isdir(trj_output_folder):
            messagebox.showwarning('Input Error',
                                     'trj split folder does not exist on the extract drive.')
            mainloop_wrapper(main_frame)

        if not os.path.isdir(os.path.join(trj_output_folder, 'GRN')):
            messagebox.showwarning('Input Error',
                                     'grn folder does not exist in the trj split folder on the extract drive.')
            mainloop_wrapper(main_frame)

        if not os.path.isdir(os.path.join(trj_output_folder, 'NIR')):
            messagebox.showwarning('Input Error',
                                     'nir folder does not exist in the trj split folder on the extract drive.')
            mainloop_wrapper(main_frame)

        for rootdir, directories, items in os.walk(monkeyed_folder):
            for item in items:
                disallowed_items = [".las", ".log", ".txt", ".xml"]
                for extension in disallowed_items:
                    if item.lower().endswith(extension):
                        messagebox.showwarning('Input Error',
                                                 '4_Monkeyed folder on the extract drive already contains output files.')
                        mainloop_wrapper(main_frame)

        if ch0las_count == 0:
            messagebox.showwarning('Input Error',
                                     'No LAS in %s ' % ch0_folder)
            mainloop_wrapper(main_frame)

        if not ch0las_count == ch1las_count:
            messagebox.showwarning('Input Error',
                                     'Filecount mismatch between grn ch0 and ch1 LAS.')
            mainloop_wrapper(main_frame)

        if not ch0las_count == nirlas_count:
            if surfaces[0] in ws_list:
                ok = messagebox.askokcancel('Input Warning',
                                              'Filecount mismatch between grn and NIR LAS.\nContinue?')
                if ok:
                    pass
                else:
                    mainloop_wrapper(main_frame)
            else:
                messagebox.showwarning('Input Error',
                                         'Filecount mismatch between grn and NIR LAS.')
                mainloop_wrapper(main_frame)

        if processing_start < 1:

            if os.path.isdir(reports_folder):
                ok = messagebox.askokcancel("Input Warning",
                                              "Reports folder for this mission already exists on the extract drive. "
                                              "Continue?")
                if ok:
                    pass
                else:
                    mainloop_wrapper(main_frame)

            for rootdir, directories, items in os.walk(trj_output_folder):
                for item in items:
                    if item.lower().endswith(".trj"):
                        messagebox.showwarning('Input Error',
                                                 'Split trj directory on the extract drive already contains TRJ.')
                        mainloop_wrapper(main_frame)

        #if processing_start == 0:
        #     # validate input traj is not in geodetic lat/lon (try to ensure it was imported correctly)
        #     if not any(".trj" in item for item in os.listdir(trj_input_folder)):
        #         messagebox.showwarning('Input Error',
        #                                  '1_traj_full folder in the 3_Trajectories folder on the extract drive '
        #                                  'does not contain TRJ.')
        #         mainloop_wrapper(main_frame)
        #     for item in os.listdir(trj_input_folder):
        #         if item.lower().endswith(".trj"):
        #             with open(os.path.join(trj_input_folder, item), 'rb') as traj:
        #                 traj.seek(12, os.SEEK_SET)
        #                 start_pt = struct.unpack('<i', traj.read(4))[0]
        #                 traj.seek(start_pt - 8, os.SEEK_CUR)
        #                 start_x = struct.unpack('<d', traj.read(8))[0]
        #                 start_y = struct.unpack('<d', traj.read(8))[0]
        #             if abs(start_x) < 180 or abs(start_y) < 180:
        #                 messagebox.showwarning('Input Error',
        #                                          'Input trajectories appear to be in geodetic coordinates.')
        #                 mainloop_wrapper(main_frame)
        #             if not 194773 <= start_x <= 805227:
        #                 messagebox.showwarning('Input Error',
        #                                          'Input trajectories have eastings outside expected range.\n '
        #                                          'Please ensure correct UTM Zone.')
        #                 mainloop_wrapper(main_frame)
        #             if not 2600000 <= start_y <= 9300000:
        #                 messagebox.showwarning('Input Error',
        #                                          'Input trajectories have northings outside expected range.\n '
        #                                          'Where in the world is Carmen Sandiego?')
        #                 mainloop_wrapper(main_frame)

    if processing_start < 5 and processing_end > 5:

        if os.path.isdir(gpl_folder):
            for item in os.listdir(gpl_folder):
                if item.lower().endswith(".las"):
                    messagebox.showwarning('Input Error',
                                             'gpch folder already contains LAS.')
                    mainloop_wrapper(main_frame)

    if processing_start < 4 and processing_end > 3:

        if os.path.isdir(import_folder):
            for item in os.listdir(import_folder):
                if item.lower().endswith(".las"):
                    messagebox.showwarning('Input Error',
                                             'imported folder already contains LAS.')
                    mainloop_wrapper(main_frame)

    if  any(n in processing_steps for n in [1, 2, 3, 4]):

        if not os.path.isdir(monkeyed_folder):
            messagebox.showwarning('Input Error',
                                     '%s does not exist.' % monkeyed_folder)
            mainloop_wrapper(main_frame)

    if any(n in processing_steps for n in [2, 3]):
        if processing_start == 2 or processing_start == 3:

            for surface, shape in shp_dict.items():
                if surface in ws_list:
                    if not os.path.isfile(shape):
                        messagebox.showwarning('Input Error',
                                               'Shapefile %s does not exist.' % shape)
                        mainloop_wrapper(main_frame)

            if not attenuation_coeff_dict[sensor]:
                messagebox.showwarning('Input Error',
                                         'Sensor %s does not have attenuation coefficient defined.\n'
                                         'Please contact Lara if you need to process this sensor.' % sensor)
                mainloop_wrapper(main_frame)
            if not int_norm_dict[sensor]:
                messagebox.showwarning('Input Error',
                                       'Sensor %s does not have intensity coefficients defined.\n'
                                       'Please contact Lara if you need to process this sensor.' % sensor)
                mainloop_wrapper(main_frame)

            grn_shpname = os.path.basename(shp_dict[surfaces[0]]).lower()
            if 'ir' in grn_shpname or 'land' in shp_dict[surfaces[0]].lower():
                ok = messagebox.askokcancel('Input Warning',
                                            'Filename "%s" is suspicious.\n Press ok to continue if this is really '
                                            'the green refraction shape.'
                                            % grn_shpname)
                if ok:
                    pass
                else:
                    mainloop_wrapper(main_frame)
            ir_shpname = os.path.basename(shp_dict[surfaces[1]]).lower()
            if 'gr' in ir_shpname or 'land' in ir_shpname:
                ok = messagebox.askokcancel('Input Warning',
                                            'Filename "%s" is suspicious.\n Press ok to continue if this is really '
                                            'the nir refraction shape.'
                                            % ir_shpname)
                if ok:
                    pass
                else:
                    mainloop_wrapper(main_frame)
            ul_shpname = os.path.basename(shp_dict[surfaces[2]]).lower()
            if 'gr' in ul_shpname or 'ir' in ul_shpname:
                ok = messagebox.askokcancel('Input Warning',
                                            'Filename "%s" is suspicious.\n Press ok to continue if this is really '
                                            'the upland refraction shape.'
                                            % ul_shpname)
                if ok:
                    pass
                else:
                    mainloop_wrapper(main_frame)
            ch0_files = file_lister(monkeyed_folder, str_filt_list=[riegl_str_dict['ch0']],
                                    ext_filt_list=['.las'], recursive=True)
            ch1_files = file_lister(monkeyed_folder, str_filt_list=[riegl_str_dict['ch1']],
                                    ext_filt_list=['.las'], recursive=True)
            nir_files = file_lister(monkeyed_folder, str_filt_list=[riegl_str_dict['nir']],
                                    ext_filt_list=['.las'], recursive=True)
            if not ch0_files or not ch1_files:
                messagebox.showwarning('Input Error',
                                         'Missing green channel 0 and/or 1 files to refract in %s.' % monkeyed_folder)
                mainloop_wrapper(main_frame)
            if not nir_files:
                messagebox.showwarning('Input Error',
                                         'Missing nir files in %s.' % monkeyed_folder)
                mainloop_wrapper(main_frame)
            if len(ch0_files) != len(ch1_files):
                messagebox.showwarning('Input Error',
                                         'Mismatch between Channel 0 and 1 LAS in %s.' % monkeyed_folder)
                mainloop_wrapper(main_frame)

            ch0las_list = create_list_of_lists_of_incremental_las(ch0_files)

            ch1las_list = create_list_of_lists_of_incremental_las(ch1_files)

            nirlas_list = create_list_of_lists_of_incremental_las(nir_files)

            if len(ch0las_list) != len(nirlas_list):
                messagebox.showwarning('Input Error',
                                         'Mismatch between GRN and NIR LAS in %s.' % monkeyed_folder)
                mainloop_wrapper(main_frame)

            if len(ch0las_list) != len(ch1las_list):
                messagebox.showwarning('Input Error',
                                         'Mismatch between Channel 0 and 1 LAS in %s.' % monkeyed_folder)
                mainloop_wrapper(main_frame)

            if len(ch0las_list) != len(nirlas_list):
                messagebox.showwarning('Input Error',
                                         'Mismatch between GRN and NIR LAS in %s.' % monkeyed_folder)
                mainloop_wrapper(main_frame)

            ###TODO add proper comparison between ch0 & ch1, make sure needed swaths are processed
            if swath_filter:
                swath_filter_list = swath_filter.replace(' ','').split(',')

                las_list = ch0las_list + ch1las_list + nirlas_list
                las_list, string_not_found_list = filter_list_by_list_of_strings(las_list, swath_filter_list, array=True)
                ch0las_list, unused_filters = filter_list_by_list_of_strings(ch0las_list, swath_filter_list, array=True)
                ch1las_list, unused_filters = filter_list_by_list_of_strings(ch1las_list, swath_filter_list, array=True)
                nirlas_list, unused_filters = filter_list_by_list_of_strings(nirlas_list, swath_filter_list, array=True)
                if len(las_list) == 0:
                    messagebox.showwarning('Input Error',
                                             'No swaths survived filtering.')
                    mainloop_wrapper(main_frame)
                if string_not_found_list:
                    ok = messagebox.askokcancel('Input Warning',
                                                  'Swath input filter(s) %s did not match any  swath files.\nContinue?'
                                                  % string_not_found_list)
                    if ok:
                        pass
                    else:
                        mainloop_wrapper(main_frame)

                ###FIXME need to figure out how to handle running individual swaths - require whole line?
                # nir_filtered_list = []
                # for item in ch0las_list:
                #     match = match_riegl_swath_names_between_scanners(item, nirlas_list, minimum_time_gap, array=True)
                #     if not match:
                #         messagebox.showwarning('Input Error',
                #                                  'Unable to find NIR swath for %s.' % os.path.basename(item[0].split('[')))
                #         mainloop_wrapper(main_frame)
                #     else:
                #         nir_filtered_list.append(match)
                # nirlas_list = nir_filtered_list
            # print('swath filter list: %s' % swath_filter_list)
            # print('ch0laslist %s' % ch0las_list)
            # print('ch1laslist %s' % ch1las_list)
            # print('nirlaslist %s' % nirlas_list)
            renamed_count = ren_ptsrcid_to_timestamp(ws_las_input_folder, monkeyed_folder, trj_output_folder, main_frame)
            if renamed_count:
                print('... renamed %s water surface files to match Riegl naming scheme ...' % renamed_count)

            if surfaces[0] in ws_list:
                ch0_ws_files = file_lister(ws_las_input_folder, str_filt_list=[riegl_str_dict['ch0']],
                                           ext_filt_list=['.las'], recursive=True)
                ch1_ws_files = file_lister(ws_las_input_folder, str_filt_list=[riegl_str_dict['ch1']],
                                           ext_filt_list=['.las'], recursive=True)
                ch0las_ws_list = create_list_of_lists_of_incremental_las(ch0_ws_files)
                ch1las_ws_list = create_list_of_lists_of_incremental_las(ch1_ws_files)

                if len(ch0las_ws_list) != len(ch1las_ws_list):
                    messagebox.showwarning('Input Error',
                                             'Mismatch between channel 0 and 1 water surface LAS in %s'
                                             % ws_las_input_folder)
                    mainloop_wrapper(main_frame)

            if processing_start == 2:

                if not os.path.isdir(ws_las_input_folder):
                    messagebox.showwarning('Input Error',
                                             'Missing folder %s.' % ws_las_input_folder)
                    mainloop_wrapper(main_frame)
                else:
                    if len(file_lister(ws_las_input_folder, ['.las'])) == 0:
                        messagebox.showwarning('Input Error',
                                                 'No LAS files in %s.' % ws_las_input_folder)
                        mainloop_wrapper(main_frame)

                #if ws_required == 1:
                las_list = file_lister(ws_las_input_folder, ext_filt_list=['.las'])
                if surfaces[0] in ws_list:
                    if not any('channel_g' in las.lower() for las in las_list):
                        messagebox.showwarning('Input Error', 'No LAS with "Ch_G" in filename in %s.\n'
                                                              'Please confirm inputs and surface selection.'
                                                 % ws_las_input_folder)
                        mainloop_wrapper(main_frame)
                if surfaces[1] in ws_list:
                    if not any('channel_ir' in las.lower() for las in las_list):
                        messagebox.showwarning('Input Error', 'No LAS with "Ch_IR" in filename in %s.\n'
                                                              'Please confirm inputs and surface selection.'
                                                 % ws_las_input_folder)
                        mainloop_wrapper(main_frame)
                if surfaces[2] in ws_list:
                    upland_las = file_lister(ws_las_input_folder, ext_filt_list=['.las'],
                                             str_filt_list=['upland'])
                    if len(upland_las) == 0:
                        messagebox.showwarning('Input Error', 'No LAS with "upland" in filename in %s.\n'
                                                              'Please confirm inputs and surface selection.'
                                                 % ws_las_input_folder)
                        mainloop_wrapper(main_frame)
                    if len(upland_las) > 1:
                        messagebox.showwarning('OBJ Error', 'More than one LAS with "upland" in filename in %s.\n'
                                                              'Please merge all upland water surfaces into one file.'
                                                 % ws_las_input_folder)
                        mainloop_wrapper(main_frame)

            if processing_start == 3:

                if not os.path.isdir(obj_folder):
                    messagebox.showwarning('Input Error',
                                             'Missing folder %s.' % obj_folder)
                    mainloop_wrapper(main_frame)
                else:
                    if not any(".obj" in item for item in os.listdir(obj_folder)):
                        messagebox.showwarning('Input Error',
                                                 'No OBJ in 5_OBJs folder on extract drive.')
                        mainloop_wrapper(main_frame)

                #if ws_required == 1:
                obj_list = file_lister(obj_folder, ext_filt_list=['.obj'])
                if surfaces[0] in ws_list:
                    if not any(riegl_str_dict['grn'] in obj.lower() for obj in obj_list):
                        messagebox.showwarning('OBJ Error', 'No OBJs with "%s" in filename in %s.\n'
                                                              'Please confirm inputs and surface selection.'
                                                 % (riegl_str_dict['grn'], obj_folder))
                        mainloop_wrapper(main_frame)
                if surfaces[1] in ws_list:
                    if not any(riegl_str_dict['nir'] in obj.lower() for obj in obj_list):
                        messagebox.showwarning('OBJ Error', 'No OBJs with "%s" in filename in %s.\n'
                                                              'Please confirm inputs and surface selection.'
                                                 % (riegl_str_dict['nir'], obj_folder))
                        mainloop_wrapper(main_frame)
                if surfaces[2] in ws_list:
                    if not any(riegl_str_dict['upland'] in obj.lower() for obj in obj_list):
                        messagebox.showwarning('OBJ Error', 'No OBJs with "%s" in filename in %s.\n'
                                                              'Please confirm inputs and surface selection.'
                                                 % (riegl_str_dict['upland'], obj_folder))
                        mainloop_wrapper(main_frame)

                ws_las_file_list = file_lister(ws_las_folder, ext_filt_list='.las')
                if not ws_las_file_list:
                    messagebox.showwarning('Water Surface Error', 'No LAS in %s\n'
                                                        'Please select OBJ as start step to create these LAS.'
                                           % ws_las_folder)
                    mainloop_wrapper(main_frame)

    if processing_start == 6:

        if not os.path.isfile(mission_gpl_macro):
            messagebox.showwarning('Input Error',
                                     'Step 1 macro does not exist in macro folder.')
            mainloop_wrapper(main_frame)

    if processing_start == 5 or processing_start == 6:

        if not os.path.isfile(imported_project):
            messagebox.showwarning('Input Error',
                                     '0_TSCAN_imported.prj does not exist in reports folder on calib drive.')
            mainloop_wrapper(main_frame)

    if processing_start == 7 or processing_start == 8:

        if not os.path.isfile(gpl_project):
            messagebox.showwarning('Input Error',
                                     '1_TSCAN_gpl.prj does not exist in reports folder on calib drive.')
            mainloop_wrapper(main_frame)

        if processing_start == 7:

            if os.path.isdir(gpl_qc_folder):
                messagebox.showwarning('Input Error',
                                         'QC folder already exists.')
                mainloop_wrapper(main_frame)

        if processing_start == 8:

            if os.path.isdir(tielines_folder):
                messagebox.showwarning('Input Error',
                                         'Tielines folder already exists.')
                mainloop_wrapper(main_frame)

    if any(n in processing_steps for n in [4, 6, 7, 8]):

        ## test for active TSKs
        make_temp_tslave_folders(tslave_progress_folder, tslave_reports_folder, tslave_task_folder, main_frame,
                                 "replace")
        if not os.path.isfile(os.path.join(temp_folder, "tslave.exe")):
            shutil.copy2(os.path.join(terra_path, "tslave", "tslave.exe"), temp_folder)
        if not os.path.isfile(os.path.join(temp_folder, "ncsecw.dll")):
            shutil.copy2(os.path.join(terra_path, "tslave", "ncsecw.dll"), temp_folder)
        if not os.path.isfile(os.path.join(temp_folder, "tslave.upf")):
            upf_contents = ["[Terra preferences]\n", "Application=TerraSlave\n",
                            "LicDir=" + os.path.join(terra_path, "license") + "\n", "LicUseServer=1\n",
                            "LicServer=10.8.0.19\n", "LicAccess=lidar13\n", "RunTasks=2\n", "MaxThreads=1\n"]
            upf_file = os.path.join(temp_folder, "tslave.upf")

            with open(upf_file, 'w') as upf:
                for line in upf_contents:
                    upf.write(line)
        folder_maker(import_folder, main_frame, "skip")

        lic = check_terra_licenses()

        if 8 in processing_steps:
            if (int(lic['tscan'][:1]) == 0 or int(lic['tslave'][:1]) == 0) and int(lic['tmatch'][:1]) == 0:
                pass
            else:
                lic_summary_string = '\n' + '\t' + 'License statuses:\n\n'
                for license in lic:
                    lic_summary_string += '\t' + license + lic[license][1:] + '\n'
                messagebox.showwarning('Input validation', 'Please ensure that there is a TerraScan or TerraSlave '
                                                             'license and a TerraMatch license checked out for at least'
                                                             ' 24 hours.\n' + lic_summary_string)
                mainloop_wrapper(main_frame)
        elif any(n in processing_steps for n in [4, 6, 7]):
            if int(lic['tscan'][:1]) == 0 or int(lic['tslave'][:1]) == 0:
                pass
            else:
                lic_summary_string = '\n' + '\t' + 'License statuses:\n\n'
                for license in lic:
                    lic_summary_string += '\t' + license + lic[license][1:] + '\n'
                messagebox.showwarning('Input validation', 'Please ensure that there is a TerraScan or TerraSlave '
                                                             'license checked out for at least'
                                                             ' 24 hours.\n' + lic_summary_string)
                mainloop_wrapper(main_frame)

    if processing_start > 0:

        split_trj_list = []
        for rootdir, directories, items in os.walk(trj_output_folder):
            for item in items:
                if item.endswith(".trj"):
                    split_trj_list.append(item)

        if not split_trj_list:
            messagebox.showwarning('Input Error',
                                             'Split trj directory in the extract location does not contain TRJ.')
            mainloop_wrapper(main_frame)

    if processing_start == 4:


        if not any(".las" in item for item in os.listdir(monkeyed_folder)):

            if not any(".las" in item for item in os.listdir(os.path.join(monkeyed_folder, "__rfx_las"))):

                messagebox.showwarning('Input Error',
                                         '4_Monkeyed folder on the extract drive does not contain LAS.')
                mainloop_wrapper(main_frame)

    if 4 in processing_steps:

        if any(".las" in item for item in os.listdir(import_folder)):
            messagebox.showwarning('Input Error',
                                     '0_imported folder on the calib drive already contains LAS.')
            mainloop_wrapper(main_frame)

    if 6 in processing_steps:

        folder_maker(gpl_folder, main_frame, "skip")
        gpl_tslave_reports_folder = os.path.join(reports_folder, "1_tslave_gpl_task_reports")
        if os.path.isdir(gpl_tslave_reports_folder):
            messagebox.showwarning('Input Error',
                                     '1_tslave_gpl_task_reports already exists. '
                                     'Please clear all outputs of previous run.')
            mainloop_wrapper(main_frame)
        if any(".las" in item for item in os.listdir(gpl_folder)):
            messagebox.showwarning('Input Error',
                                     '1_gpl folder on the calib drive already contains LAS.')
            mainloop_wrapper(main_frame)

    if 8 in processing_steps:

        folder_maker(tielines_folder, main_frame, "skip")
        tieline_tslave_reports_folder = os.path.join(reports_folder, "1_tslave_tieline_task_reports")
        if os.path.isdir(tieline_tslave_reports_folder):
            messagebox.showwarning('Input Error',
                                     '1_tslave_tieline_task_reports already exists. '
                                     'Please clear all outputs of previous run.')
            mainloop_wrapper(main_frame)

    if 7 in processing_steps:

        folder_maker(gpl_qc_folder, main_frame, "skip")
        qc_tslave_reports_folder = os.path.join(reports_folder, "1_tslave_qc_task_reports")
        if os.path.isdir(qc_tslave_reports_folder):
            messagebox.showwarning('Input Error',
                                     '1_tslave_qc_task_reports already exists. '
                                     'Please clear all outputs of previous run.')
            mainloop_wrapper(main_frame)

    if processing_start == 0:

        # attempt to create a lock in the traj folder so only one instance can be splitting trajs at a time
        while True:
            if locker(trj_lock_file, email, mission_name, socket.gethostname()) == "lock created":
                # logger("Lock created in " + all_trj_dir + "\n\n")
                break
            elif locker(trj_lock_file, email, mission_name, socket.gethostname()) == "trajectories locked":
                print("Trajectory editing locked by another process.")
                time.sleep(15)
                continue

        # validate traj override & get starting flightline number
        flightline_list = []
        for item in os.listdir(all_trj_dir):
            if ".trj" in item:
                if "GRN" in item:
                    with open(os.path.join(all_trj_dir, item), 'rb') as trajectory:
                        trajectory.read(124)
                        flightline_number = struct.unpack('<i', trajectory.read(4))[0]
                        flightline_list.append(flightline_number)

        if trj_start_override != "trj start # override" or None:
            if not str.isdigit(trj_start_override):
                messagebox.showwarning('Input Error',
                                         'Trj start # override specified is not a valid integer.')
                mainloop_wrapper(main_frame)
            split_line_list = []
            flightline_number = int(trj_start_override)
            if flightline_number < int(grn_number_start):
                if os.path.isdir(reports_folder):
                    ok = messagebox.askokcancel('Input Warning',
                                                  'Trj start # override specified is less than the'
                                                  ' default project start # of'
                                                  + grn_number_start + 'Continue?')
                    if ok:
                        pass
                    else:
                        mainloop_wrapper(main_frame)
            if flightline_number in flightline_list:
                messagebox.showwarning('Input Error',
                                         'Trj start # override specified is already in use'
                                         ' in project trajectories folder.')
                mainloop_wrapper(main_frame)
            split_line_list.append(flightline_number)
            test_flightline_number = flightline_number
            for i in range(ch0las_count):
                split_line_list.append(test_flightline_number)
                test_flightline_number += 1
            existing_line_set = set(flightline_list)
            desired_line_set = set(split_line_list)
            if existing_line_set & desired_line_set:
                messagebox.showwarning('Input Error',
                                         'Based on number of input LAS files, trj start # override'
                                         ' specified would cause duplication of line numbers.')
                mainloop_wrapper(main_frame)
            grn_number_start = str(flightline_number)
        else:
            if flightline_list:
                grn_number_start = str(int(round((max(flightline_list) + 15), -1)))

        ### clean this placement up
        folder_maker(temp_folder, main_frame, "skip")

    main(main_frame, IC_folder, mission_name, email, deltek_id, project_name, agl,
         sensor, trj_buffer_size, tail_clip, grn_number_start, spool_up_time, speed, processing_start, processing_end,
         threads, las_monkey_file_path, lastools_path, terra_path, ws_required, optional_qc,
         green_ch0_las_monkey_config, green_ch1_las_monkey_config, nir_las_monkey_config, rfx_las_monkey_config,
         tscan_project_template, tieline_settings_file, terra_transform_file, terra_ptc_file, gpl_macro_template,
         all_trj_dir, ICer_folder, mission_number, mission_date, trj_input_folder,
         trj_output_folder, exported_folder, monkeyed_folder, obj_folder, calib_trj_folder, reports_folder, import_folder,
         gpl_folder, tielines_folder, gpl_qc_folder, temp_folder, tslave_progress_folder, tslave_reports_folder,
         tslave_task_folder, import_project, imported_project, gpl_project, mission_gpl_macro, trj_lock_file,
         ws_las_folder, rfx_folder, ch0las_list, ch1las_list, nirlas_list, ws_las_input_folder, minimum_time_gap,
         riegl_str_dict, surfaces, ws_list, shp_dict, attenuation_coeff_dict, int_norm_dict, concavity, run_start_time)



def main(main_frame, IC_folder, mission_name, email, deltek_id, project_name, agl,
         sensor, trj_buffer_size, tail_clip, grn_number_start, spool_up_time, speed, processing_start, processing_end,
         threads, las_monkey_file_path, lastools_path, terra_path, ws_required, optional_qc,
         green_ch0_las_monkey_config, green_ch1_las_monkey_config, nir_las_monkey_config, rfx_las_monkey_config,
         tscan_project_template, tieline_settings_file, terra_transform_file, terra_ptc_file, gpl_macro_template,
         all_trj_dir, ICer_folder, mission_number, mission_date, trj_input_folder,
         trj_output_folder, exported_folder, monkeyed_folder, obj_folder, calib_trj_folder, reports_folder, import_folder,
         gpl_folder, tielines_folder, gpl_qc_folder, temp_folder, tslave_progress_folder, tslave_reports_folder,
         tslave_task_folder, import_project, imported_project, gpl_project, mission_gpl_macro, trj_lock_file,
         ws_las_folder, rfx_folder, ch0las_list, ch1las_list, nirlas_list, ws_las_input_folder, minimum_time_gap,
         riegl_str_dict, surfaces, ws_list, shp_dict, attenuation_coeff_dict, int_norm_dict, concavity, run_start_time):
    print("Input validation completed sucessfully! Carry on :)\n\n")

    # hardcoded gpl vars
    neighbors = '105.00'  # meters

    # hardcoded traj vars
    nir_numbering_step_value = '10000'

    # water surface classes
    ws_classes = {surfaces[0]: ['28','41'], surfaces[1]: ['9', '28'], surfaces[2]: ['9', '28', '41']}

    # get sys info
    dispatcher = socket.gethostname()

    # set var to store which step the ICer is on
    processing_step = processing_start

    # set up processing log and function to write to it
    icer_log = os.path.join(reports_folder, "__Refraction_Wrapper_Log__Run_%s.txt" % run_start_time)

    # set up folders created by script
    temp_monkeyed_folder = os.path.join(monkeyed_folder, "__temp_las") #deprecated
    #rfx_folder = os.path.join(ICer_folder, "3_rfx_las")
    qsd_folder = os.path.join(rfx_folder, "QSDs")
    ch0_folder = os.path.join(exported_folder, "ChG_0")
    ch1_folder = os.path.join(exported_folder, "ChG_1")
    nir_folder = os.path.join(exported_folder, "ChIR")
    #ws_las_folder = os.path.join(ICer_folder, "1_ws_las")
    #merged_ws_las_folder = os.path.join(ws_las_folder, "__merged")
    #ch0_monkeyed_folder = os.path.join(monkeyed_folder, "ChG_0")
    #ch1_monkeyed_folder = os.path.join(monkeyed_folder, "ChG_1")
    #nir_monkeyed_folder = os.path.join(monkeyed_folder, "Ch_IR")
    #folder_maker(temp_monkeyed_folder, main_frame, "skip")
    #folder_maker(qsd_folder, main_frame, "skip")
    #folder_maker(merged_ws_las_folder, main_frame, "replace")

    # set up path to lastools binaries
    ### make validator check explicitly for these? bundle lastools?
    lasmerge_filepath = os.path.join(lastools_path, "lasmerge.exe")
    las2tin_filepath = os.path.join(lastools_path, "las2tin.exe")
    blast2dem_filepath = os.path.join(lastools_path, "blast2dem.exe")
    lasoverlap_filepath = os.path.join(lastools_path, "lasoverlap.exe")
    lasgrid_filepath = os.path.join(lastools_path, "lasgrid64.exe")
    las2las_filepath = os.path.join(lastools_path, "las2las64.exe")

    def logger(contents):
        with open(icer_log, 'a') as log:
            log.write(contents)

    # set up a function to launch lastools
    def lastools_launcher(icer_command, process_name, folder_name, parent_folder, threads):
        start_time = time.time()
        exe = os.path.split(icer_command[0])[1]
        logger("#" * 50 + " " + process_name + " (" + exe + ") Log:\n\n")
        output_folder = os.path.join(parent_folder, folder_name)
        folder_maker(output_folder, main_frame, "replace")
        icer_command.append("-odir")
        icer_command.append(output_folder)
        icer_command.append("-cores")
        icer_command.append(threads)
        icer_stdout, icer_stderr = subprocess.Popen(icer_command, stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE).communicate()
        logger(exe + ' standard output messages:\n\n')
        if icer_stdout:
            logger(icer_stdout + "\n")
        else:
            logger("None \n\n")
        logger(exe + ' standard error messages:\n\n')
        if icer_stderr:
            logger(icer_stderr + "\n")
        else:
            logger("None \n\n")
        end_time = time.time()
        duration = format(end_time - start_time, '.1f')
        logger(process_name + ' took ' + str(duration) + ' seconds\n\n')

    # go
    logger("#" * 50 + " NEW RUN STARTED " + run_start_time + " " + "#" * 50 + "\n\n")
    logger("Mission: " + mission_name + "\n")
    logger("Script version: " + version + "\n")
    logger("Dispatcher: " + dispatcher + "\n")
    logger("Username:" + email + "\n")
    logger("Instances: " + threads + "\n")
    logger("\n")
    print("NEW RUN STARTED %s\n\n" % run_start_time)

    if processing_step == 2:
        logger("#" * 50 + " OBJ Generation (las2tin.exe) Log:\n\n")
        start_time = time.time()
        print("Generating " + mission_name + " OBJs...")
        folder_maker(obj_folder, main_frame, "skip")

        # incremental_list = []
        # full_swath_list = []
        # for item in os.listdir(ws_las_folder):
        #     if item.lower().endswith('.las'):
        #         if "[" in item:
        #             name = item.split('[')[0]
        #             if not name in incremental_list:
        #                 incremental_list.append(name)
        #         else:
        #             full_swath_list.append(item)
        # incremental_counter = len(incremental_list)
        # full_swath_counter = len(full_swath_list)
        #
        # las_list_file = os.path.join(ws_las_folder, 'las2tin_input_file_list.txt')
        # ws_source_tags = []
        # if ws_source == 'GRN':
        #     ws_source_tags = ['channel_g']
        # elif ws_source == 'NIR':
        #     ws_source_tags = ['channel_ir']
        # elif ws_source == 'G+IR':
        #     ws_source_tags = ['channel_g','channel_ir']
        # ws_source_folder = ws_las_input_folder
        # temp_obj_folder = ws_las_folder
        #
        # def list_las2tin_inputs(ws_las_folder):
        #     with open(las_list_file, 'w') as list:
        #         for item in os.listdir(ws_las_folder):
        #             if item.lower().endswith('.las'):
        #                 for tag in ws_source_tags:
        #                     if tag in item.lower():
        #                         list.write(os.path.join(ws_las_folder, item) + "\n")
        #
        # if incremental_counter > 0 and full_swath_counter > 0:
        #     messagebox.showwarning('Error', 'G+IR incremental and full-swath las files present in %s.' % ws_las_folder)
        #     print('Error: G+IR incremental and full-swath las files present in %s.' % ws_las_folder)
        #     print('Processing stopped')
        #     mainloop_wrapper(main_frame)
        #
        # elif incremental_counter > 0 and full_swath_counter == 0:
        #     incremental_las_merger(ws_las_folder)
        #     temp_obj_folder = merged_ws_las_folder
        #     list_las2tin_inputs(merged_ws_las_folder)
        #     ws_count = incremental_counter
        #
        # elif incremental_counter == 0 and full_swath_counter > 0:
        #     with open(las_list_file, 'w') as list:
        #         for item in os.listdir(ws_las_folder):
        #             if item.lower().endswith('.las'):
        #                 for tag in ws_source_tags:
        #                     if tag in item.lower():
        #                         list.write(os.path.join(ws_las_folder, item) + "\n")
        #
        #
        # elif incremental_counter == 0 and full_swath_counter == 0:
        #     las2las_command_list = []
        #     for item in os.listdir(ws_source_folder):
        #         if item.lower().endswith('.las'):
        #             las_file = os.path.join(ws_source_folder, item)
        #             las2las_command = [las2las_filepath, "-i", las_file, "-odir", ws_las_folder, "-keep_extended_class"]
        #             las2las_command.append(ws_classes[ws_source])
        #             las2las_command_list.append(las2las_command)
        #     temp_obj_folder = merged_ws_las_folder
        #
        #     batch_commands(las2las_command_list, threads)
        #
        #     incremental_las_merger(ws_las_folder)

        ws_las_list = file_lister(ws_las_input_folder, str_filt_list=['Channel_G', 'Channel_IR', 'land'],
                                  ext_filt_list=['.las'])

        print('... outputting LAS containing only water surface to %s folder ...'
              % os.path.basename(os.path.normpath(ws_las_folder)))
        las2las_command_list = []
        for item in ws_las_list:
            las2las_command = [las2las_filepath, "-i", item, "-odir", ws_las_folder, "-keep_extended_class"]
            for classification in ws_classes[surfaces[2]]:
                las2las_command.append(classification)
            #las2las_command.append(ws_classes[ws_source])
            las2las_command_list.append(las2las_command)
        batch_commands(las2las_command_list, threads)

        for las in file_lister(ws_las_folder, ext_filt_list=['.las']):
            size = int(os.path.getsize(las))
            if size < 378:
                os.remove(las)
                print('... ignored 0pt file: %s ...' % las)

        temp_obj_folder = ws_las_folder

        ws_only_las_list = file_lister(ws_las_folder, ext_filt_list=['.las'])

        if len(ws_only_las_list) == 0:
            print('No water surface LAS exist for OBJ creation!)')
            print('Processing stopped!')
            messagebox.showwarning('Error',
                                     'No water surface LAS exist for OBJ creation.\n ')
            mainloop_wrapper(main_frame)

        print('... creating OBJ files ...')
        las2tin_command_list = []
        for las in ws_only_las_list:
            las2tin_command = [las2tin_filepath, "-i", las, "-odir", obj_folder, '-concavity', concavity, '-oobj',
                               "-keep_extended_class"]
            for classification in ws_classes[surfaces[2]]:
                las2tin_command.append(classification)
            #las2tin_command.append(ws_classes[ws_source])
            las2tin_command_list.append(las2tin_command)
        batch_commands(las2tin_command_list, threads)
        # las2tin_command = [las2tin_filepath, '-lof', las_list_file, '-odir', obj_folder, '-concavity', '50', '-oobj',
        #                    '-keep_extended_class']
        # las2tin_command += ws_classes[ws_source]
        # lastools_launcher(las2tin_command, 'Create OBJs', os.path.basename(obj_folder), IC_folder, threads)

        end_time = time.time()
        duration = format(end_time - start_time, '.1f')

        ### FIX when LasTools updated
        time.sleep(5)
        obj_list = os.listdir(obj_folder)
        if not any('.obj' in item for item in obj_list):
            try:
                temp_folder_contents = os.listdir(temp_obj_folder)
                for item in temp_folder_contents:
                    if '.obj' in item:
                        if not '[' in item:
                            shutil.copy(os.path.join(temp_obj_folder, item), obj_folder)
                            os.remove(os.path.join(temp_obj_folder, item))
                time.sleep(5)
            except:
                print('Unable to move .obj files from temp_las folder')
                print('Process stopped.')
                messagebox.showwarning('Input Error', 'Unable to move .obj files from temp_las folder on  '
                                                        'extract drive.')
                mainloop_wrapper(main_frame)

        for obj in obj_list:
            obj_path = os.path.join(obj_folder, obj)
            obj_size = int(os.path.getsize(obj_path))
            if obj_size < 102: #2049:
                print('Empty OBJs exist.')
                print('Process stopped.')
                messagebox.showwarning('OBJ Error', 'Empty OBJs exist. Please ensure that all swaths in %s\n'
                                                      'have water surface points present.' % ws_las_input_folder)
                mainloop_wrapper(main_frame)

        # if ws_required == 1:
        #     ch0las_list = []
        #     for item in os.listdir(ch0_monkeyed_folder):
        #         if item.lower().endswith(".las"):
        #             if 'channel_g_0' in item.lower():
        #                 name = item.split('[')[0].replace('.las','')
        #                 if not name in ch0las_list:
        #                     ch0las_list.append(name)
        #     ch0las_count = len(ch0las_list)
        #
        #     ch1las_list = []
        #     for item in os.listdir(ch1_monkeyed_folder):
        #         if item.lower().endswith(".las"):
        #             if 'channel_g_1' in item.lower():
        #                 name = item.split('[')[0].replace('.las','')
        #                 if not name in ch1las_list:
        #                     ch1las_list.append(name)
        #     ch1las_count = len(ch1las_list)
        #
        #     nirlas_list = []
        #     for item in os.listdir(nir_monkeyed_folder):
        #         if item.lower().endswith(".las"):
        #             if 'channel_g_1' in item.lower():
        #                 name = item.split('[')[0].replace('.las','')
        #                 if not name in nirlas_list:
        #                     nirlas_list.append(name)
        #     nirlas_count = len(ch1las_list)
        #
        #     if ch1las_count != ch0las_count:
        #         messagebox.showwarning('LAS Error', 'Mismatch between number of ch0 & ch1 LAS in Monkeyed folder.')
        #         print('Mismatch between number of ch0 & ch1 LAS in Monkeyed folder.')
        #         print('Process stopped.')
        #         mainloop_wrapper(main_frame)
        #
        #     if ws_source == 'NIR':
        #         if ws_required:
        #             if nirlas_count != ch0las_count:
        #                 if ch1las_count != ch0las_count:
        #                     messagebox.showwarning('LAS Error',
        #                                              'Mismatch between number if ch0 & nir LAS in Monkeyed folder.')
        #                     print('Mismatch between number of ch0 & nir LAS in Monkeyed folder.')
        #                     print('Process stopped.')
        #                     mainloop_wrapper(main_frame)
        #
        #     obj_list = os.listdir(obj_folder)
        #     obj_count = 0
        #     for file in obj_list:
        #         if file.lower().endswith('.obj'):
        #             obj_count += 1
        #
        #     if ws_source == 'NIR':
        #         if obj_count != ch0las_count:
        #             messagebox.showwarning('OBJ Error', 'Mismatch between number of OBJs and number of flightlines. '
        #                                                   'Please ensure that all flightlines have water '
        #                                                   'surface points present.')
        #             print('Mismatch between number of OBJs and number of flightlines.')
        #             print('Process stopped.')
        #             mainloop_wrapper(main_frame)
        #     if ws_source == 'GRN':
        #         if obj_count != (2 * ch0las_count):
        #             messagebox.showwarning('OBJ Error', 'Mismatch between number of OBJs and number of swaths. '
        #                                                   'Please ensure that all swaths have water '
        #                                                   'surface points present.')
        #             print('Mismatch between number of OBJs and number of swaths.')
        #             print('Process stopped.')
        #             mainloop_wrapper(main_frame)
        #     if ws_source == 'G+IR':
        #         if  (2 * ch0las_count) < obj_count < ch0las_count:
        #             messagebox.showwarning('OBJ Error', 'Mismatch between number of OBJs and number of swaths. '
        #                                                   'Please ensure that all swaths have water '
        #                                                   'surface points present.')
        #             print('Mismatch between number of OBJs and number of swaths.')
        #             print('Process stopped.')
        #             mainloop_wrapper(main_frame)

        logger("OBJ generation took " + str(duration) + " seconds \n\n")
        print("OBJ generation complete (took %s seconds)!\n\n" % duration.rstrip())
        if processing_step == processing_end:
            logger("#" * 50 + " RUN COMPLETE    " + datetime.now().strftime('%Y%m%d_%H%M%S') + " " + "#" * 50 + "\n\n")
            print("RUN COMPLETE " + datetime.now().strftime('%Y%m%d_%H%M%S'))
            mainloop_wrapper(main_frame)
        processing_step = 3

    if processing_step == 3:
        logger("#" * 50 + " Las Monkey Refraction, Normalization & Intensity Filtering (LasMonkey.exe) Log:\n\n")
        start_time = time.time()

        print("Refracting " + mission_name + " ...")

        to_run_las_list = ch0las_list + ch1las_list + nirlas_list
        to_run_las_list.sort()

        skip_rfx_list = []

        temp_merged_to_refract_folder = os.path.join(ICer_folder, '01_temp_to_refract___')
        folder_maker(temp_merged_to_refract_folder, main_frame, 'replace')

        temp_rfx_folder = os.path.join(rfx_folder, '__temp_rfx_folder')
        folder_maker(temp_rfx_folder, main_frame, 'replace')

        rfx_lm_command_list = []
        rfx_lm_command_log = os.path.join(temp_merged_to_refract_folder, "rfx_lm_commands.txt")

        list_counter = 0

        def check_for_obj_match(swath, obj_folder, surfaces):
            obj_list = file_lister(obj_folder, ext_filt_list=['.obj'])
            swath_name = os.path.basename(swath)
            swath_time = datetime.strptime(swath[0:13], "%y%m%d_%H%M%S")
            obj_match_list = []
            for item in obj_list:
                if 'upland' in item.lower():
                    obj_match_list.append(item)
                else:
                    obj_name = os.path.basename(item)
                    obj_time = datetime.strptime(obj_name[0:13], "%y%m%d_%H%M%S")
                    delta = int(abs(obj_time - swath_time).total_seconds())
                    if delta <= int(minimum_time_gap):
                        if riegl_str_dict['ch0'] in swath_name.lower() and riegl_str_dict['ch0'] in obj_name.lower():
                            obj_match_list.append(item)
                        elif riegl_str_dict['ch1'] in swath_name.lower() and riegl_str_dict['ch1'] in obj_name.lower():
                            obj_match_list.append(item)
                        elif riegl_str_dict[surfaces[1]] in obj_name.lower():
                            obj_match_list.append(item)
                        elif surfaces[2] in obj_name.lower():
                            obj_match_list.append(item)
            return(obj_match_list)
        print('... merging input files into swaths ...')
        incremental_las_merger(to_run_las_list, temp_merged_to_refract_folder, lasmerge_filepath, threads)
        to_run_las_list = file_lister(temp_merged_to_refract_folder, ext_filt_list=['.las'])

        for las in to_run_las_list:
            swath = os.path.basename(las)
            obj_list = []
            if riegl_str_dict['grn'] in swath.lower():
                obj_list = check_for_obj_match(swath, obj_folder, surfaces)
                if len(obj_list) == 0:
                    if ws_required == 1:
                        print('Not all swaths have an OBJ with matching name.')
                        print('Process stopped.')
                        messagebox.showwarning('OBJ Error', 'Please ensure that each swath has matching '
                                                              'OBJ file(s) with a timestamp in the filename matches '
                                                              'to within %ss.' % minimum_time_gap)
                        mainloop_wrapper(main_frame)
                    else:
                        ###TODO skip nir that don't have water surface
                        skip_rfx_list.append(las)
                        continue
                else:
                    grn_objs = filter_list_by_list_of_strings(obj_list, [riegl_str_dict['grn']])[0]
                    if len(grn_objs) > 1:
                        print('Multiple possible OBJ matches found')
                        print('Process stopped.')
                        messagebox.showwarning('OBJ Error', 'Multiple possible green OBJ matches found for %s. Please '
                                                            'ensure correct surface type(s) are selected\nand '
                                                            'each swath has only one OBJ where the '
                                                            'timestamp in the filename matches to within'
                                                            ' %ss.' % (las, minimum_time_gap))
                        mainloop_wrapper(main_frame)
                    nir_objs = filter_list_by_list_of_strings(obj_list, [riegl_str_dict['nir']])[0]
                    if len(nir_objs) > 1:
                        print('Multiple possible OBJ matches found')
                        print('Process stopped.')
                        messagebox.showwarning('OBJ Error', 'Multiple possible green OBJ matches found for %s. Please '
                                                            'ensure correct surface type(s) are selected\nand '
                                                            'each swath has only one OBJ where the '
                                                            'timestamp in the filename matches to within'
                                                            ' %ss.' % (las, minimum_time_gap))
                        mainloop_wrapper(main_frame)

            rfx_steps = get_refraction_xml_steps(sensor, las, obj_list, riegl_str_dict, shp_dict, surfaces, ws_list,
                                                 os.path.join(trj_output_folder, 'GRN'), attenuation_coeff_dict,
                                                 int_norm_dict)
            xml_contents = get_xml(dispatcher, rfx_steps, ws_las_folder)

            xml_filepath = os.path.join(temp_merged_to_refract_folder,
                                        "__NOAA_%s_RFX_Config.xml" % swath.replace('.las',''))
            with open(xml_filepath, 'w') as xml:
                xml.write(xml_contents)
            rfx_lm_command = [las_monkey_file_path, '-cfg', xml_filepath, '-userid', email, '-projid',
                              deltek_id, '-cores', '4', '-ifile', las, '-auto', '-noupdate', '-nolog'] # '-o', rfx_folder]
            with open(rfx_lm_command_log, 'a') as log:
                log.write("command " + str(list_counter) + ":")
                command  = ''
                for item in rfx_lm_command:
                    command += (item + ' ')
                log.write(command)
                log.write('\n\n')
            rfx_lm_command_list.append(rfx_lm_command)
            list_counter += 1

        if skip_rfx_list:
            for item in skip_rfx_list:
                logger('Skipping refraction for %s (no matching water surface)\n' % os.path.basename(item))
                print('... skipping refraction for %s (no matching water surface) ...' % os.path.basename(item))

        for i in range(len(rfx_lm_command_list)):
            rfx_lm_command_list[i].append('-o')
            output_folder = os.path.join(temp_rfx_folder, str(i))
            rfx_lm_command_list[i].append(output_folder)
            folder_maker(output_folder, main_frame, 'replace')

        command_index = 0
        batches = -(-len(rfx_lm_command_list) // int(threads)) # using negative signs and integer division to round up
        for i in range(batches):
            #output_folder = os.path.join(temp_rfx_folder, str(i))
            barrel = []
            for j in range(int(threads)):
                if command_index >= len(rfx_lm_command_list):
                    break
                # check to make sure that any pending Las Monkey instances have finished launching before proceeding
                ready = False
                while not ready:
                    lm_config_list = []
                    ###TODO how to solve this issue better? this is a nonissue now isn't it?
                    for rootdir, directories, items in os.walk(temp_rfx_folder):
                        for item in items:
                            if item.endswith("_config.xml"):
                                lm_config_list.append(os.path.join(temp_rfx_folder, item))
                        ready = True if len(lm_config_list) == command_index else False
                    time.sleep(2)

                # launch a Las Monkey instance
                monkey = subprocess.Popen(rfx_lm_command_list[command_index])
                time.sleep(2)
                barrel.append(monkey)
                command_index += 1

            logger(str(datetime.now()) + ": Running batch " + str(i + 1) + " of " + str(batches) + " through Las Monkey refraction\n")

            for monkey in barrel:
                monkey.wait()

        ### TODO include code to ID each log and strip redundant lines?
        lm_log_list = file_lister(rfx_folder, ext_filt_list=['.log'], recursive=True)

        if not lm_log_list:
            print('Las Monkey did not run.')
            print('Process stopped.')
            messagebox.showwarning('Las Monkey Error',
                                     'Las Monkey processes did not run.')
            mainloop_wrapper(main_frame)
        lm_log_list.sort()
        lm_warnings_list = []
        lm_errors_list = []
        for log_filepath in lm_log_list:
            log_name = os.path.basename(log_filepath)
            lm_log_lines_list = []
            with open(log_filepath, 'r') as log:
                for line in log:
                    if "Warning:" in line:
                        if "Writing zero-point LAS file." in line or "ReferenceLas... No matching fragment" in line or "no matching Reference file" in line:
                            pass
                        else:
                            lm_warnings_list.append('From %s -- %s' % (log_name, line))
                    if "Error:" in line or "Allocation" in line:
                        lm_errors_list.append('From %s -- %s' % (log_name, line))
                    lm_log_lines_list.append(line)
            for line in lm_log_lines_list:
                if 'processing log. Search' in line:
                    line = ''
                if '"Warning" and "Error" to find messages requiring attention.' in line:
                    line = ''
                logger(line)
            logger("\n\n")

        # move rfx results out of subfolders
        for rootdir, directories, files in os.walk(temp_rfx_folder):
            for file in files:
                try:
                    srcpath = os.path.join(rootdir, file)
                    destpath = os.path.join(rfx_folder, file)
                    shutil.move(srcpath, destpath)
                except:
                    pass

        print('... copying swaths that skipped refraction from temp folder into refracted folder ...')
        for las in skip_rfx_list:
            shutil.copy2(las, rfx_folder)
        # for item in skip_rfx_list:
        #     with open(item, 'r') as list:
        #         for las in list:
        #             shutil.copy2(las.strip(), rfx_folder)

        if surfaces[2] in ws_list:
            print('... copying upland synthetic water surface points into refracted folder ...')
            upland_ws_las = file_lister(ws_las_folder, )
            las2las_command = [las2las_filepath, "-i", upland_ws_las, "-odir", rfx_folder, "-keep_extended_class",
                               "28"]
            upland_stdout, upland_stderr = subprocess.Popen(las2las_command, stdout=subprocess.PIPE,
                                                        stderr=subprocess.PIPE).communicate()

        #print('Removing temporary folders ...')
        #shutil.rmtree(temp_merged_to_refract_folder)
        #shutil.rmtree(temp_rfx_folder)
        if optional_qc:
            # create rfx qc rasters
            print("... 'output intermediate qc layers after refraction' was checked - creating post-rfx QC rasters ...")

            rfx_qc_folder = os.path.join(rfx_folder, '__qc')

            las_list = os.path.join(rfx_folder, "lastools_input_file_list.txt")
            file_lister_to_txt(rfx_folder, las_list)

            nir_int_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "1", "-fill", "3",  "-keep_user_data", "3",
                                        "-intensity", "-average", "-first_only", "-oasc", "-merged"]
            lastools_launcher(nir_int_icer_command, "NIR Intensity Raster",
                              "nir_int_1m", rfx_qc_folder, threads)

            refracted_w_wh_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "1", "-fill",
                                           "3", "-keep_extended_class", "24", "26", "45", "40", "173", "-drop_user_data",
                                           "3", "-point_density", "-otif", "-merged"]
            lastools_launcher(refracted_w_wh_icer_command, "Refracted Green Point Density Raster (Includes Clip)",
                              "refracted_1m", rfx_qc_folder, threads)

            unrefracted_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "1", "-fill", "3",
                                        "-drop_extended_class", "24", "26", "45", "40", "173", "-drop_user_data", "3",
                                        "-point_density", "-otif", "-merged"]
            lastools_launcher(unrefracted_icer_command, "Unrefracted Green Point Density Raster",
                              "unrefracted_1m", rfx_qc_folder, threads)

            refracted_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "1", "-fill", "3",
                                      "-drop_extended_class", "24", "26", "45", "40", "173", "-drop_user_data", "3",
                                      "-point_density", "-otif", "-merged"]
            lastools_launcher(refracted_icer_command, "Refracted Green Point Density Raster",
                              "refracted_clipped_1m", rfx_qc_folder, threads)

            lh_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "1", "-fill", "3", "-drop_extended_class",
                               "129", "173", "-elevation", "-lowest", "-otif", "-merged", "-drop_z_below", "-100"]
            lastools_launcher(lh_icer_command, "Lowest Hit Raster", "lh_1m", rfx_qc_folder, threads)

            hh_rfx_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "1", "-fill", "3", "-keep_extended_class",
                               "40", "45", "173", "-elevation", "-highest", "-otif", "-merged", "-drop_z_below", "-100"]
            lastools_launcher(hh_rfx_icer_command, "Highest Hit Rfx Raster", "hh_rfx_1m", rfx_qc_folder, threads)

            hh_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "1", "-fill", "3", "-drop_user_data",
                               "3", "-elevation", "-highest", "-otif", "-merged", "-drop_z_below", "-100"]
            lastools_launcher(hh_icer_command, "Highest Hit Raster", "hh_1m", rfx_qc_folder, threads)

            dz_values_icer_command = [lasoverlap_filepath, "-lof", las_list, "-step", "1", "-no_over", "-last_only",
                                      "-keep_extended_class", "1", "32", "26", "45", "-values", "-otif"]
            lastools_launcher(dz_values_icer_command, "DZ Orthos Raster", "dz_1m", rfx_qc_folder, threads)

            ch0_rfx_ol_icer_command = [lasoverlap_filepath, "-lof", las_list, "-step", "1", "-no_diff", "-keep_user_data",
                                       "0", "-keep_extended_class", "24", "26", "45", "40", "173", "-values", "-otif"]
            lastools_launcher(ch0_rfx_ol_icer_command, "Ch0 Rfx OL Raster", "ch0ol_1m", rfx_qc_folder, threads)

            ch1_rfx_ol_icer_command = [lasoverlap_filepath, "-lof", las_list, "-step", "1", "-no_diff", "-keep_user_data",
                                       "1",  "-keep_extended_class", "24", "26", "45", "40", "173", "-values", "-otif"]
            lastools_launcher(ch1_rfx_ol_icer_command, "Ch1 Rfx OL Raster", "ch1ol_1m", rfx_qc_folder, threads)

            # be_icer_command = [blast2dem_filepath, "-lof", las_list, "-step", "1", "-keep_extended_class", "26", "32",
            #                    "-otif", "-merged"]
            # lastools_launcher(be_icer_command, "DEM Raster", "be_1m", rfx_qc_folder, threads)

            wsm_icer_command = [blast2dem_filepath, "-lof", las_list, "-step", "1", "-otif", "-merged",
                                "-keep_extended_class"]
            wsm_icer_command.append(ws_classes[surfaces[2]])
            lastools_launcher(wsm_icer_command, "WS Raster", "wsm_1m", rfx_qc_folder, threads)

        print('... checking Las Monkey reports for warnings and errors...')
        if lm_warnings_list:
            with open(os.path.join(reports_folder, "__Refraction_Wrapper_LAS_MONKEY_WARNINGS_%s.txt" % run_start_time),
                      'a') as warning_log:
                warning_log.write("The following warnings were encountered during Las Monkey processing "
                                  "(review the %s log or individual LasMonkey notification logs for details):\n" % title)
                for line in lm_warnings_list:
                    warning_log.write(line)

        if lm_errors_list:
            with open(os.path.join(reports_folder, "__Refraction_Wrapper_LAS_MONKEY_ERRORS_%s.txt" % run_start_time),
                      'a') as error_log:
                error_log.write("The following errors were encountered during Las Monkey processing "
                                  "(review the %s log or individual LasMonkey notification logs for details):\n" % title)
                for line in lm_errors_list:
                    error_log.write(line)
            print('Las Monkey encountered error(s) during processing.\nPlease review the log.')
            print('Process stopped.')
            messagebox.showwarning('Las Monkey Error',
                                     'Las Monkey encountered error(s) during processing.\nPlease review the log.')
            mainloop_wrapper(main_frame)

        end_time = time.time()
        duration = format(end_time - start_time, '.1f')
        logger("Las Monkey Refraction, Depth Normalization & Intensity Filtering took " + str(duration) + " seconds \n\n")
        print("Las Monkey processes complete (took %s seconds)!\n\n" % str(duration))

        if processing_step == processing_end:
            logger("#" * 50 + " RUN COMPLETE    " + datetime.now().strftime('%Y%m%d_%H%M%S') + " " + "#" * 50 + "\n\n")
            print("RUN COMPLETE " + datetime.now().strftime('%Y%m%d_%H%M%S'))
            mainloop_wrapper(main_frame)
        processing_step = 4

    if processing_step == 4:
        # import points

        print("Importing " + mission_name + " ...")

        import_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        start_time = time.time()

        process_name = "Import"
        logger("#" * 50 + " " + process_name + " (tslave.exe) Log:\n\n")

        import_project_contents = []
        block_count = 0

        with open(tscan_project_template, 'r') as prj:
            for line in prj:
                import_project_contents.append(line)

        for line in import_project_contents:
            if "Directory=" in line:
                index = import_project_contents.index(line)
                import_project_contents[index] = "Directory=" + import_folder + "\n"
            if "Trajectories=" in line:
                index = import_project_contents.index(line)
                import_project_contents[index] = "Trajectories=" + calib_trj_folder + "\n"

        with open(import_project, 'w') as prj:
            for line in import_project_contents:
                prj.write(line)

        while True:
            lic = check_terra_licenses()
            if int(lic['tscan'][:1]) < 2 or int(lic['tslave'][:1]) < 2:
                break
            else:
                lic_summary_string = '\n\tLicense statuses:\n\n'
                for license in lic:
                    lic_summary_string += '\t' + license + lic[license][1:] + '\n'
                    ok = messagebox.askokcancel('TSlave Import Warning', 'Please ensure that there is a '
                                                                           'TerraScan/TerraSlave license checked out for '
                                                                           'at least 24 hours.\n' + lic_summary_string +
                                                  'Press ok to continue.')
                    if ok:
                        continue
                    else:
                        mainloop_wrapper(main_frame)

        import_task_file = os.path.join(tslave_task_folder, import_timestamp + ".tsk")
        import_filelist = []
        import_filecount = 0
        import_pointcount = 0

        for item in os.listdir(rfx_folder):
            if os.path.splitext(item.lower())[-1] == ".las":
                import_filelist.append(os.path.join(rfx_folder, item) + "\n")
                import_filecount += 1

        import_filelist.sort()

        for item in import_filelist:
            item = item.rstrip()
            with open(item, 'rb') as las:
                las.seek(247, os.SEEK_SET)
                number_of_point_records = struct.unpack('<Q', las.read(8))[0]
                import_pointcount += number_of_point_records

        import_task_contents = ["[TerraSlave task]\n", "Task=tscan_project_import\n", "Dispatcher=" + dispatcher + "\n",
                                "ProcessBy=" + dispatcher + "\n", "Project=" + import_project + "\n",
                                "Progress=" + tslave_progress_folder + "\n", "Reports=" + tslave_reports_folder + "\n",
                                "ImportFormat=44\n", "ImportSrcTime=1\n\n", "ImportTotalCount=", str(import_pointcount)
                                + "\n\n", "[Files]\n", "Count=" + str(import_filecount) + "\n"]

        with open(import_task_file, 'w') as task:
            for line in import_task_contents:
                task.write(line)
            for line in import_filelist:
                task.write(line)

        my_command = os.path.join(temp_folder, "tslave.exe")
        os.startfile(my_command)

        while True:
            if os.path.isfile(import_task_file):
                time.sleep(15)
            else:
                break

        import_report_file = os.path.join(tslave_reports_folder, import_timestamp + ".txt")
        import_report_lines = []

        logger(process_name + " error messages:\n\n")
        error_count = 0
        with open(import_report_file, 'r') as report:
            for line in report:
                if "points were ignored" in line:
                    if line[0] != "0":
                        error_count += 1
                        logger(line + " during import.\n")
                        with open(os.path.join(reports_folder, "__Refraction_Wrapper_log_IMPORT_ERRORS_RUN_%s.txt" %
                                               run_start_time), 'a') as error_log:
                            error_log.write("\t\t" + line + "during import.\n")
                        print("Error: some points were ignored.")
                        break
                if "Status=Failed" in line:
                    error_count += 1
                    logger("\t\t" + "TerraSlave import failed.\n")
                    with open(os.path.join(reports_folder, "__Refraction_Wrapper_log_IMPORT_ERRORS_RUN_%s.txt" %
                                           run_start_time), 'a') as error_log:
                        error_log.write("TerraSlave import failed.\n")
                    print("Error: TSlave import failed.")
                    break
                if "Status=Aborted" in line:
                    error_count += 1
                    logger("TerraSlave aborted during import.\n")
                    with open(os.path.join(reports_folder, "__Refraction_Wrapper_log_IMPORT_ERRORS_RUN_%s.txt" %
                                                           run_start_time ), 'a') as error_log:
                        error_log.write("\t\t" + "TerraSlave aborted during import.\n")
                    print("Error: TSlave import aborted.")
                    break
                import_report_lines.append(line)

        if error_count == 0:
            logger("None\n\n")

        import_report_file_output = os.path.join(reports_folder,
                                                 "0_tslave_import_task_report__run_%s.txt" % run_start_time)
        import_task_file_output = os.path.join(reports_folder,
                                               "0_tslave_import_task_file__run_%s.tsk" % run_start_time)

        with open(import_report_file_output, 'w') as report:
            for line in import_report_lines:
                report.write(line)

        with open(import_task_file_output, 'w') as task:
            for line in import_task_contents:
                task.write(line)
            for line in import_filelist:
                task.write(line)

        # shutil.rmtree(tslave_reports_folder)
        # os.makedirs(tslave_reports_folder)

        block_list = os.listdir(import_folder)

        imported_project_contents = []
        in_header = True

        with open(import_project, 'r') as project:
            for line in project:
                if in_header:
                    imported_project_contents.append(line)
                    if line in ["\n", "\r\n"]:
                        in_header = False
                if "Block " in line:
                    if line.replace("Block", "").strip() in block_list:
                        imported_project_contents.append(line)
                        for l in range(8):
                            imported_project_contents.append(project.next())
                        block_count += 1

        end_time = time.time()
        duration = format(end_time - start_time, '.1f')
        logger(process_name + " took " + str(duration) + " seconds to create " + str(block_count) +
               " bins from " + str(import_filecount) + " swath files\n\n")
        print("import complete (took %s seconds to create %s bins from %s swath files)!"
              % (duration.rstrip(), str(block_count), str(import_filecount)))

        with open(imported_project, 'w') as prj:
            for line in imported_project_contents:
                prj.write(line)

        if processing_step == processing_end:
            logger("#" * 50 + " RUN COMPLETE    " + datetime.now().strftime('%Y%m%d_%H%M%S') + " " + "#" * 50 + "\n\n")
            print("RUN COMPLETE " + datetime.now().strftime('%Y%m%d_%H%M%S'))
            mainloop_wrapper(main_frame)
        processing_step = 5

    if processing_step == 5:

        print("Generating " + mission_name + " GPL macro...")

        process_name = "GPL Macro Creation"
        logger("#" * 50 + " " + process_name + " Log:\n\n")
        start_time = time.time()

        knots_to_mps_factor = 0.514444  # knots/(meter/second)

        start_line_list = []
        start_clip_list = []
        end_clip_list = []
        end_line_list = []

        start_clip_distance = 2 * math.tan(math.radians(20)) * int(agl) + trj_buffer_size * speed * knots_to_mps_factor\
                              + tail_clip
        print("... total distance to clip from beginning of lines: %sm ..." % start_clip_distance)
        end_clip_distance = 2 * math.tan(math.radians(20)) * int(agl) + (trj_buffer_size + spool_up_time)\
                            * speed * knots_to_mps_factor + tail_clip
        print("... total distance to clip from end of lines: %sm ..." % end_clip_distance)

        filecount = 0
        ### TODO move this to validate step so short trajs are caught up front? or validate timestamps of las files?
        ### TODO sort this
        for rootdir, directories, items in os.walk(os.path.join(trj_output_folder, "GRN")):
            for item in items:
                if item.lower().endswith(".trj"):
                    filecount += 1
                    print("... reading trajectory: %s ..." % item)
                    with open(os.path.join(rootdir, item), 'rb') as traj:
                        traj.seek(12, os.SEEK_SET)
                        start_pt = struct.unpack('<i', traj.read(4))[0]
                        number_of_records = struct.unpack('<i', traj.read(4))[0]
                        #print("# records=", number_of_records)

                        distance = 0
                        traj.seek(start_pt - 20, os.SEEK_CUR)
                        start_timestamp = struct.unpack('<d', traj.read(8))[0]
                        start_line_list.append(start_timestamp)
                        #print("start time is:", start_timestamp)
                        start_x = struct.unpack('<d', traj.read(8))[0]
                        #print("start x is:", start_x)
                        start_y = struct.unpack('<d', traj.read(8))[0]
                        #print("start y is:", start_y)

                        traj.seek(48, os.SEEK_CUR)

                        for index in range(number_of_records - 1):
                            x = struct.unpack('<d', traj.read(8))[0]
                            y = struct.unpack('<d', traj.read(8))[0]
                            dd = math.sqrt((x - start_x) ** 2 + (y - start_y) ** 2)
                            distance = distance + dd
                            start_x = x
                            start_y = y
                            if distance < start_clip_distance:
                                traj.seek(-24, os.SEEK_CUR)
                                timestamp = struct.unpack('<d', traj.read(8))[0]
                                traj.seek(64, os.SEEK_CUR)
                            else:
                                break

                        if distance < start_clip_distance:
                            ### make this a warning log!!!!!!!!!!!!!!!!!!!!!!!!!
                            messagebox.showwarning("Tail Clip Error",
                                                     "Trajectory " + item + " too short.")
                            mainloop_wrapper(main_frame)

                        start_clip_list.append(timestamp)
                        #print("start clip distance is: ", distance)

                        distance = 0
                        traj.seek(-64, os.SEEK_END)
                        end_timestamp = struct.unpack('<d', traj.read(8))[0]
                        end_line_list.append(end_timestamp)
                        #print("end time is: ", end_timestamp)
                        end_x = struct.unpack('<d', traj.read(8))[0]
                        #print("end x is:", end_x)
                        end_y = struct.unpack('<d', traj.read(8))[0]
                        #print("end y is:", end_y)

                        traj.seek(-80, os.SEEK_CUR)

                        for index in range(number_of_records - 1):
                            x = struct.unpack('<d', traj.read(8))[0]
                            y = struct.unpack('<d', traj.read(8))[0]
                            dd = math.sqrt((x - end_x) ** 2 + (y - end_y) ** 2)
                            distance = distance + dd
                            end_x = x
                            end_y = y
                            if distance < end_clip_distance:
                                traj.seek(-24, os.SEEK_CUR)
                                timestamp = struct.unpack('<d', traj.read(8))[0]
                                traj.seek(-64, os.SEEK_CUR)
                            else:
                                break

                        end_clip_list.append(timestamp)
                        #print("end clip distance is:", distance)
                    if distance < end_clip_distance:
                        messagebox.showwarning('Tail Clip Error',
                                                 'Trajectory ' + item + ' too short.')
                        print('GPL macro encountered errors: trajectory ' + item + ' too short.\n'
                                                                                   'Please review and restart')
                        print('Process stopped.')
                        mainloop_wrapper(main_frame)


        mission_macro_contents = []

        with open(gpl_macro_template, 'r') as macro:
            for line in macro:
                mission_macro_contents.append(line)

        macro_index = 0

        ## do G+IR in one?
        for line in mission_macro_contents:
            if "#---------------------- tail clip ---------------------" in line:
                macro_index += 1
                break
            macro_index += 1

        for line in mission_macro_contents:
            if "FnScanOutput" in line:
                index = mission_macro_contents.index(line)
                mission_macro_contents[index] = "FnScanOutput(\"" + os.path.join(gpl_folder, "#block.las")\
                                                + "\",\"Any\",44,0,3,\"\",-1,0,1,\"2\")\n"

        # macro_class_map = {173:163, 129:139, 45:21, 41:59, 1:11}
        ### fix this so it is an iterable class list!!!!!!!!!!!

        def write_class_by_time_step(class_from, class_to, filecount, start_clip, end_clip):
            clip_times = []
            for trj in range(filecount):
                clip_times.append(
                    "FnScanClassifyTime(%i,%i,%f,%f,0)\n" % (class_from, class_to, start_clip[trj], end_clip[trj]))
            return clip_times

        class_153_end_clip = write_class_by_time_step(173, 243, filecount, end_clip_list, end_line_list)
        mission_macro_contents[macro_index:macro_index] = class_153_end_clip

        class_153_start_clip = write_class_by_time_step(173, 243, filecount, start_line_list, start_clip_list)
        mission_macro_contents[macro_index:macro_index] = class_153_start_clip

        mission_macro_contents[macro_index:macro_index] = "#\n"

        class_129_end_clip = write_class_by_time_step(129, 199, filecount, end_clip_list, end_line_list)
        mission_macro_contents[macro_index:macro_index] = class_129_end_clip

        class_129_start_clip = write_class_by_time_step(129, 199, filecount, start_line_list, start_clip_list)
        mission_macro_contents[macro_index:macro_index] = class_129_start_clip

        mission_macro_contents[macro_index:macro_index] = "#\n"

        class_45_end_clip = write_class_by_time_step(45, 125, filecount, end_clip_list, end_line_list)
        mission_macro_contents[macro_index:macro_index] = class_45_end_clip

        class_45_start_clip = write_class_by_time_step(45, 125, filecount, start_line_list, start_clip_list)
        mission_macro_contents[macro_index:macro_index] = class_45_start_clip

        mission_macro_contents[macro_index:macro_index] = "#\n"

        class_41_end_clip = write_class_by_time_step(41, 121, filecount, end_clip_list, end_line_list)
        mission_macro_contents[macro_index:macro_index] = class_41_end_clip

        class_41_start_clip = write_class_by_time_step(41, 121, filecount, start_line_list, start_clip_list)
        mission_macro_contents[macro_index:macro_index] = class_41_start_clip

        mission_macro_contents[macro_index:macro_index] = "#\n"

        class_37_end_clip = write_class_by_time_step(37, 117, filecount, end_clip_list, end_line_list)
        mission_macro_contents[macro_index:macro_index] = class_37_end_clip

        class_37_start_clip = write_class_by_time_step(37, 117, filecount, start_line_list, start_clip_list)
        mission_macro_contents[macro_index:macro_index] = class_37_start_clip

        mission_macro_contents[macro_index:macro_index] = "#\n"

        class_32_end_clip = write_class_by_time_step(32, 112, filecount, end_clip_list, end_line_list)
        mission_macro_contents[macro_index:macro_index] = class_32_end_clip

        class_32_start_clip = write_class_by_time_step(32, 112, filecount, start_line_list, start_clip_list)
        mission_macro_contents[macro_index:macro_index] = class_32_start_clip

        mission_macro_contents[macro_index:macro_index] = "#\n"

        class_26_end_clip = write_class_by_time_step(26, 96, filecount, end_clip_list, end_line_list)
        mission_macro_contents[macro_index:macro_index] = class_26_end_clip

        class_26_start_clip = write_class_by_time_step(26, 96, filecount, start_line_list, start_clip_list)
        mission_macro_contents[macro_index:macro_index] = class_26_start_clip

        mission_macro_contents[macro_index:macro_index] = "#\n"

        class_24_end_clip = write_class_by_time_step(24, 94, filecount, end_clip_list, end_line_list)
        mission_macro_contents[macro_index:macro_index] = class_24_end_clip

        class_24_start_clip = write_class_by_time_step(24, 94, filecount, start_line_list, start_clip_list)
        mission_macro_contents[macro_index:macro_index] = class_24_start_clip

        mission_macro_contents[macro_index:macro_index] = "#\n"

        class_9_end_clip = write_class_by_time_step(9, 79, filecount, end_clip_list, end_line_list)
        mission_macro_contents[macro_index:macro_index] = class_9_end_clip

        class_9_start_clip = write_class_by_time_step(9, 79, filecount, start_line_list, start_clip_list)
        mission_macro_contents[macro_index:macro_index] = class_9_start_clip

        mission_macro_contents[macro_index:macro_index] = "#\n"

        class_1_end_clip = write_class_by_time_step(1, 71, filecount, end_clip_list, end_line_list)
        mission_macro_contents[macro_index:macro_index] = class_1_end_clip

        class_1_start_clip = write_class_by_time_step(1, 71, filecount, start_line_list, start_clip_list)
        mission_macro_contents[macro_index:macro_index] = class_1_start_clip

        # mission_macro_contents[macro_index:macro_index] = "#\n"

        mission_macro_contents[macro_index:macro_index] = "# clip times based on %sm AGL, %skn speed, " \
                                                          "%ss spool-up time, "\
                                                          "%ss trj buffer, and %sm add'l clip\n" \
                                                          % (agl, str(speed), str(spool_up_time),
                                                             str(trj_buffer_size), str(tail_clip))

        with open(mission_gpl_macro, 'w') as mission_macro:
            for line in mission_macro_contents:
                mission_macro.write(line)

        end_time = time.time()
        duration = format(end_time - start_time, '.1f')
        logger(process_name + " took " + str(duration) + " seconds\n\n")
        print("Done writing macro (took %s seconds)!\n\n" % duration)

        if processing_step == processing_end:
            logger("#" * 50 + " RUN COMPLETE    " + datetime.now().strftime('%Y%m%d_%H%M%S') + " " + "#" * 50 + "\n\n")
            print("RUN COMPLETE " + datetime.now().strftime('%Y%m%d_%H%M%S'))
            mainloop_wrapper(main_frame)
        processing_step = 6

    if processing_step == 6:

        print("Grounding " + mission_name + " per line...")

        gpl_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        start_time = time.time()
        process_name = "GPL"
        logger("#" * 50 + " " + process_name + " (tslave.exe) Log:\n\n")

        make_temp_tslave_folders(tslave_progress_folder, tslave_reports_folder, tslave_task_folder,
                                 main_frame, "replace")

        gpl_task_file = os.path.join(tslave_task_folder, gpl_timestamp + ".tsk")

        ## do this better
        block_count = 0
        with open(imported_project, 'r') as project:
            for line in project:
                if "Block " in line:
                    block_count += 1

        gpl_task_contents = ["[TerraSlave task]\n", "Task=tscan_macro\n", "Macro=" + mission_gpl_macro + "\n",
                             "SaveResults=0\n", "Neighbours=" + neighbors + "\n", "NeedMatch=0\n",
                             "Dispatcher=" + dispatcher + "\n", "ProcessBy=" + dispatcher + "\n",
                             "Project=" + imported_project + "\n", "Blocks=1-" + str(block_count) + "\n",
                             "PointClasses=" + terra_ptc_file + "\n",
                             "Transformations=" + terra_transform_file + "\n", "Progress=" + tslave_progress_folder +
                             "\n", "Reports=" + tslave_reports_folder + "\n"]

        mission_gpl_macro_copy = os.path.join(reports_folder, "1_NOAA_step_1_" + mission_name + ".mac")

        mission_macro_contents = []

        with open(mission_gpl_macro, 'r') as macro:
            for line in macro:
                mission_macro_contents.append(line)

        with open(mission_gpl_macro_copy, 'w') as macro:
            for line in mission_macro_contents:
                macro.write(line)

        while True:
            lic = check_terra_licenses()
            if int(lic['tscan'][:1]) < 2 or int(lic['tslave'][:1]) < 2:
                break
            else:
                lic_summary_string = '\n' + '\t' + 'License statuses:\n\n'
                for license in lic:
                    lic_summary_string += '\t' + license + lic[license][1:] + '\n'
                    ok = messagebox.askokcancel('TSlave Import Warning', 'Please ensure that there is a '
                                                                           'TerraScan/TerraSlave license checked out for '
                                                                           'at least 24 hours.\n' + lic_summary_string +
                                                  'Press ok to continue.')
                    if ok:
                        continue
                    else:
                        mainloop_wrapper(main_frame)

        tslave_launcher(processing_step, processing_start, processing_end, threads, temp_folder, main_frame)

        with open(gpl_task_file, 'w') as task:
            for line in gpl_task_contents:
                task.write(line)

        while True:
            if os.path.isfile(gpl_task_file):
                time.sleep(30)
            else:
                break

        #gpl_tslave_reports_folder = os.path.join(reports_folder, "1_tslave_gpl_task_reports")
        #os.makedirs(gpl_tslave_reports_folder)

        ## add rerun steps
        logger(process_name + " error messages:\n\n")
        gpl_master_log_file = os.path.join(reports_folder, "1_tslave_gpch_master_report__run_%s.txt" % run_start_time)
        error_count = 0
        reports = file_lister(tslave_reports_folder, ext_filt_list=['.log'])
        for report in reports:
            tslave_log_lines_list = []
            with open(report, 'r') as report:
                for line in report:
                    if "Block" in line:
                        block_name = line.replace("Block ", "")
                    if "Status=Failed" in line:
                        error_count += 1
                        logger("\TerraSlave failed on " + block_name + "\n")
                        with open(os.path.join(reports_folder, "__Refraction_Wrapper_GPCH_ERRORS_RUN_%s.txt"
                                                               % run_start_time), 'a') as error_log:
                            error_log.write("TerraSlave failed on " + block_name)
                        print("Error: TSlave gpch failed.")
                    if "Status=Aborted" in line:
                        error_count += 1
                        logger("TerraSlave aborted on " + block_name + "\n")
                        with open(os.path.join(reports_folder, "__Refraction_Wrapper_GPCH_ERRORS_RUN_%s.txt"
                                                               % run_start_time), 'a') as error_log:
                            error_log.write("TerraSlave aborted on " + block_name)
                        print("Error: TSlave gpch aborted.")
                    tslave_log_lines_list.append(line)
            with open(gpl_master_log_file, 'a') as log:
                for line in tslave_log_lines_list:
                    log.write(line)
                log.write("\n\n")
                # shutil.copy2(os.path.join(tslave_reports_folder,file), gpl_tslave_reports_folder)

        if error_count == 0:
            logger("None\n\n")

        gpl_task_file_output = os.path.join(reports_folder, "1_tslave_gpch_task_file__run_%s.tsk" % run_start_time)

        with open(gpl_task_file_output, 'w') as task:
            for line in gpl_task_contents:
                task.write(line)

        gpl_project_contents = []

        imported_project_contents = []
        with open(imported_project, 'r') as project:
            for line in project:
                imported_project_contents.append(line)

        for line in imported_project_contents:
            if "Directory=" in line:
                line = "Directory=" + gpl_folder + "\n"
            if "Trajectories=" in line:
                line = "Trajectories=" + calib_trj_folder + "\n"
            gpl_project_contents.append(line)

        with open(gpl_project, 'w') as project:
            for line in gpl_project_contents:
                project.write(line)

        # ## make this actually re-run failures
        # import_size = 0
        # for item in os.listdir(import_folder):
        #     if item.endswith(".las"):
        #         b = os.path.getsize(os.path.join(import_folder, item))
        #         import_size = import_size + b
        #
        # gpl_size = 0
        # for item in os.listdir(gpl_folder):
        #     if item.endswith(".las"):
        #         b = os.path.getsize(os.path.join(gpl_folder, item))
        #         gpl_size = import_size + b
        #
        # print import_size
        # print gpl_size
        # if gpl_size != import_size:
        #     ok = messagebox.askokcancel("GPL Warning",
        #                                   "Size mismatch between import and gpl tiles.")
        #     if ok:
        #         pass
        #     else:
        #         mainloop_wrapper(main_frame)

        # shutil.rmtree(tslave_reports_folder)
        # os.makedirs(tslave_reports_folder)

        end_time = time.time()
        duration = format(end_time - start_time, '.1f')
        logger(process_name + " took " + str(duration) + " seconds\n\n")
        print("Initial grounding complete (took %s seconds)!\n\n" % duration)

        if processing_step == processing_end:
            logger("#" * 50 + " RUN COMPLETE    " + datetime.now().strftime('%Y%m%d_%H%M%S') + " " + "#" * 50 + "\n\n")
            print("RUN COMPLETE " + datetime.now().strftime('%Y%m%d_%H%M%S'))
            mainloop_wrapper(main_frame)
        processing_step = 7


    if processing_step == 7:

        # create gpl qc rasters
        print("Creating " + mission_name + " QC rasters...")

        process_name = "Output QC Rasters"
        logger("#" * 50 + " " + process_name + " (tslave.exe) Log:\n\n")

        make_temp_tslave_folders(tslave_progress_folder, tslave_reports_folder, tslave_task_folder, main_frame,
                                 "replace")

        # densities_qc_folder = os.path.join(gpl_qc_folder, "densities")
        # os.makedirs(densities_qc_folder)
        refracted_qc_folder = os.path.join(gpl_qc_folder, "%s_pc_rfx_1m" % mission_name)
        folder_maker(refracted_qc_folder, main_frame, 'replace')
        unrefracted_qc_folder = os.path.join(gpl_qc_folder, "%s_pc_unrfx_1m" % mission_name)
        folder_maker(unrefracted_qc_folder, main_frame, 'replace')
        rfx_no_wh_qc_folder = os.path.join(gpl_qc_folder, "%s_pc_rfx_no_wh_1m" % mission_name)
        folder_maker(rfx_no_wh_qc_folder, main_frame, 'replace')
        dens_qc_folder = os.path.join(gpl_qc_folder, "%s_density_1m" % mission_name)
        folder_maker(dens_qc_folder, main_frame, 'replace')
        # native_qc_folder = os.path.join(densities_qc_folder, "%s_native_10m" % mission_name)
        # os.makedirs(native_qc_folder)
        withheld_qc_folder = os.path.join(gpl_qc_folder, "%s_pc_wh_1m" % mission_name)
        folder_maker(withheld_qc_folder, main_frame, 'replace')
        # bldg_qc_folder = os.path.join(densities_qc_folder, "%s_bldg_2m" % mission_name)
        # os.makedirs(bldg_qc_folder)
        gnd_qc_folder = os.path.join(gpl_qc_folder, "%s_pc_gnd_1m" % mission_name)
        folder_maker(gnd_qc_folder, main_frame, 'replace')
        default_qc_folder = os.path.join(gpl_qc_folder, "%s_pc_default_1m" % mission_name)
        folder_maker(default_qc_folder, main_frame, 'replace')
        bathy_qc_folder = os.path.join(gpl_qc_folder, "%s_pc_bathy_1m" % mission_name)
        folder_maker(bathy_qc_folder, main_frame, 'replace')
        noise_qc_folder = os.path.join(gpl_qc_folder, "%s_pc_noise_1m" % mission_name)
        folder_maker(noise_qc_folder, main_frame, 'replace')
        nir_ws_qc_folder = os.path.join(gpl_qc_folder, "%s_pc_9_1m" % mission_name)
        folder_maker(nir_ws_qc_folder, main_frame, 'replace')
        grn_ws_qc_folder = os.path.join(gpl_qc_folder, "%s_pc_41_1m" % mission_name)
        folder_maker(grn_ws_qc_folder, main_frame, 'replace')
        synth_ws_qc_folder = os.path.join(gpl_qc_folder, "%s_pc_28_1m" % mission_name)
        folder_maker(synth_ws_qc_folder, main_frame, 'replace')

        # intensities_qc_folder = os.path.join(gpl_qc_folder, "intensities")
        # os.makedirs(intensities_qc_folder)
        # int_grn_firsts_qc_folder = os.path.join(intensities_qc_folder, "%s_int_firsts_1m" % mission_name)
        # os.makedirs(int_grn_firsts_qc_folder)
        # int_grn_lasts_qc_folder = os.path.join(intensities_qc_folder, "%s_int_lasts_1m" % mission_name)
        # os.makedirs(int_grn_lasts_qc_folder)
        # int_2_40_qc_folder = os.path.join(intensities_qc_folder, "%s_int_2_40_1m" % mission_name)
        # os.makedirs(int_2_40_qc_folder)
        # int_nir_qc_folder = os.path.join(intensities_qc_folder, "%s_int_nir_1m" % mission_name)
        # os.makedirs(int_nir_qc_folder)

        # surfaces_qc_folder = os.path.join(gpl_qc_folder, "surfaces")
        # folder_maker(surfaces_qc_folder, main_frame, 'replace')
        be_qc_folder = os.path.join(gpl_qc_folder, "%s_be_0pt5m" % mission_name)
        folder_maker(be_qc_folder, main_frame, 'replace')
        hh_qc_folder = os.path.join(gpl_qc_folder, "%s_hh_1m" % mission_name)
        folder_maker(hh_qc_folder, main_frame, 'replace')
        rfx_hh_qc_folder = os.path.join(gpl_qc_folder, "%s_hh_rfx_1m" % mission_name)
        folder_maker(rfx_hh_qc_folder, main_frame, 'replace')
        lh_qc_folder = os.path.join(gpl_qc_folder, "%s_lh_1m" % mission_name)
        folder_maker(lh_qc_folder, main_frame, 'replace')
        # lh_no_wh_qc_folder = os.path.join(surfaces_qc_folder, "%s_lh_no_wh_0pt5m" % mission_name)
        # os.makedirs(lh_no_wh_qc_folder)
        wsm_qc_folder = os.path.join(gpl_qc_folder, "%s_wsm_1m" % mission_name)
        folder_maker(wsm_qc_folder, main_frame, 'replace')
        wshh_qc_folder = os.path.join(gpl_qc_folder, "%s_hh_ws_1m" % mission_name)
        folder_maker(wshh_qc_folder, main_frame, 'replace')

        ## do this better
        block_count = 0
        with open(imported_project, 'r') as project:
            for line in project:
                if "Block " in line:
                    block_count += 1

        qc_macro = os.path.join(reports_folder, "1_NOAA_step_1_qc_" + mission_name +".mac")
        qc_macro_contents = ["[TerraScan macro]\n",
                             "Version=riegl_ic_launcher\n",
                             "Description=export qc ascs\n",
                             "Author=LH\n",
                             "ByLine=0\n",
                             "ByScanner=0\n",
                             "NeedTrajectories=0\n",
                             "SlaveCanRun=1\n",
                             "AnotherComputerCanRun=1\n",
                             "CanBeDistributed=1\n", "\n"]

        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(refracted_qc_folder,"#block.asc") +
                                 "\",\"40,45,173,183\",4,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(rfx_no_wh_qc_folder, "#block.asc") +
                                 "\",\"40,45\",4,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(unrefracted_qc_folder,"#block.asc") +
                                 "\",\"1,2,6,7,41,129,139\",4,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(be_qc_folder,"#block.asc") +
                                 "\",\"2,40\",3,\"2\",0.500,500.000,8,1,0,\"-999.999\",3,1)\n")
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(hh_qc_folder,"#block.asc") +
                                 "\",\"1,2,6,40,41,45\",2,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(rfx_hh_qc_folder,"#block.asc") +
                                 "\",\"40,45\",2,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(lh_qc_folder,"#block.asc") +
                                 "\",\"1,2,6,7,40,41,45,47,129,139,173,183\",0,\"2\",1.0,3.000,8,1,0,"
                                 "\"-999.999\",3,1)\n")
        # qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(lh_no_wh_qc_folder, "#block.asc") +
        #                          "\",\"1,2,6,40,41,45\",0,\"2\",0.500,3.000,8,1,0,"
        #                          "\"-999.999\",3,1)\n")
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(wsm_qc_folder,"#block.asc") +
                                 "\",\"%s\",3,\"2\",1,500.000,8,1,0,\"-999.999\",3,1)\n" % ws_classes[surfaces[2]])
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(wshh_qc_folder,"#block.asc") +
                                 "\",\"%s\",2,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n" % ws_classes[surfaces[2]])
        # qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(bldg_qc_folder,"#block.asc") +
        #                          "\",\"6\",4,\"2\",2.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(gnd_qc_folder,"#block.asc") +
                                 "\",\"2\",4,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(default_qc_folder,"#block.asc") +
                                 "\",\"1\",4,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(bathy_qc_folder,"#block.asc") +
                                 "\",\"40\",4,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(noise_qc_folder,"#block.asc") +
                                 "\",\"7,47\",4,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(nir_ws_qc_folder,"#block.asc") +
                                 "\",\"9\",4,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(grn_ws_qc_folder,"#block.asc") +
                                 "\",\"41\",4,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(synth_ws_qc_folder,"#block.asc") +
                                 "\",\"28\",4,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(withheld_qc_folder,"#block.asc") +
                                 "\",\"129,139,173,183\",4,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        # qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(int_nir_qc_folder,"#block.asc") +
        #                          "\",\"11,12\",9,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        # qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(int_2_40_qc_folder,"#block.asc") +
        #                          "\",\"2,40\",9,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(dens_qc_folder,"#block.asc") +
                                 "\",\"1,2,40,41,45\",4,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")

        ### fix this
        # temp_class_map = {1:51, 2:52, 6:56, 40:90, 41:91, 45:95}
        # class_firsts_step_list = []
        # class_lasts_step_list = []
        # reclass_list = []
        # temp_classes = ""
        # for original_class, temp_class in temp_class_map.items():
        #     class_firsts_step_list.append("FnScanClassifyEcho(" + str(original_class) + "," + str(temp_class)
        #                                   + ",11,0)\n")
        #     class_lasts_step_list.append("FnScanClassifyEcho(" + str(original_class) + "," + str(temp_class)
        #                                   + ",13,0)\n")
        #     reclass_list.append("FnScanClassifyClass(" + str(original_class) + "," + str(temp_class)
        #                                   + ",0)\n")
        #     if temp_classes:
        #         temp_classes += ("," + str(temp_class))
        #     else:
        #         temp_classes += str(temp_class)
        #
        # qc_macro_contents.extend(class_firsts_step_list)
        # qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(int_grn_firsts_qc_folder,"#block.asc") +
        #                          "\",\"" + temp_classes + "\",9,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        # qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(native_qc_folder,"#block.asc") +
        #                          "\",\"" + temp_classes + "\",5,\"2\",10.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        # qc_macro_contents.extend(reclass_list)
        # qc_macro_contents.extend(class_lasts_step_list)
        # qc_macro_contents.append("FnScanExportLattice(\"" + os.path.join(int_grn_lasts_qc_folder,"#block.asc") +
        #                          "\",\"" + temp_classes + "\",9,\"2\",1.000,3.000,8,1,0,\"-999.999\",3,1)\n")
        # qc_macro_contents.extend(reclass_list)

        with open(qc_macro, 'w') as macro:
            for line in qc_macro_contents:
                macro.write(line)

        qc_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        start_time = time.time()
        qc_task_file = os.path.join(tslave_task_folder, qc_timestamp + ".tsk")

        while True:
            lic = check_terra_licenses()
            if int(lic['tscan'][:1]) < 2 or int(lic['tslave'][:1]) < 2:
                break
            else:
                lic_summary_string = '\n' + '\t' + 'License statuses:\n\n'
                for license in lic:
                    lic_summary_string += '\t' + license + lic[license][1:] + '\n'
                    ok = messagebox.askokcancel('TSlave Import Warning', 'Please ensure that there is a '
                                                                           'TerraScan/TerraSlave license checked out for '
                                                                           'at least 24 hours.\n' + lic_summary_string +
                                                  'Press ok to continue.')
                    if ok:
                        continue
                    else:
                        mainloop_wrapper(main_frame)

        print("... outputting QC rasters with TerraSlave ...")

        ### modify neighbors?
        qc_task_contents = ["[TerraSlave task]\n",
                            "Task=tscan_macro\n",
                            "Macro=" + qc_macro + "\n",
                            "SaveResults=0\n",
                            "Neighbours=0.00\n",
                            "NeedMatch=0\n",
                            "NeedClasses=0\n",
                            "Dispatcher=" + dispatcher + "\n",
                            "ProcessBy=" + dispatcher + "\n",
                            "Project=" + gpl_project + "\n",
                            "Blocks=1-" + str(block_count) + "\n",
                            "Trajectories=" + calib_trj_folder + "\n",
                            "PointClasses=" + terra_ptc_file + "\n",
                            "Transformations=" + terra_transform_file + "\n",
                            "Progress=" + tslave_progress_folder + "\n",
                            "Reports=" + tslave_reports_folder + "\n"]

        tslave_launcher(processing_step, processing_start, processing_end, threads, temp_folder, main_frame)

        with open(qc_task_file, 'w') as task:
            for line in qc_task_contents:
                task.write(line)

        while True:
            if os.path.isfile(qc_task_file):
                time.sleep(30)
            else:
                break

        #qc_tslave_reports_folder = os.path.join(reports_folder, "1_tslave_qc_task_reports")
        #os.makedirs(qc_tslave_reports_folder)
        ## add rerun steps

        qc_master_log_file = os.path.join(reports_folder, "1_tslave_qc_master_report__run_%s.txt" % run_start_time)

        logger(process_name + " TerraSlave error messages:\n\n")
        error_count = 0
        reports = file_lister(tslave_reports_folder, ext_filt_list=['.log'])
        for report in reports:
            qc_log_lines_list = []
            with open(report, 'r') as report:
                for line in report:
                    if "Block" in line:
                        block_name = line.replace("Block ", "")
                    if "Status=Failed" in line:
                        error_count += 1
                        logger("TerraSlave failed on " + block_name + "\n")
                        with open(os.path.join(reports_folder, "__Refraction_Wrapper_QC_ERROR_RUN_%s.txt"
                                                               % run_start_time), 'a') as error_log:
                            error_log.write("TerraSlave failed on " + block_name)
                        print("Error: TSlave qc failed.")
                    if "Status=Aborted" in line:
                        error_count += 1
                        logger("TerraSlave aborted on " + block_name + "\n")
                        with open(os.path.join(reports_folder, "__Refraction_Wrapper_QC_ERROR_RUN_%s.txt"
                                                               % run_start_time), 'a') as error_log:
                            error_log.write("TerraSlave aborted on " + block_name)
                        print("Error: TSlave qc aborted.")
                    qc_log_lines_list.append(line)
            with open(qc_master_log_file, 'a') as log:
                for line in qc_log_lines_list:
                    log.write(line)
                log.write("\n\n")
                #shutil.copy2(os.path.join(tslave_reports_folder, file), qc_tslave_reports_folder)

        if error_count == 0:
            logger("None\n\n")

        qc_task_file_output = os.path.join(reports_folder, "1_tslave_qc_task_file__run_%s.tsk" % run_start_time)

        with open(qc_task_file_output, 'w') as task:
            for line in qc_task_contents:
                task.write(line)

        print("... outputting QC rasters with LasTools ...")

        # create lof for lastools input
        las_list = os.path.join(temp_folder, "lastools_input_file_list.txt")
        file_lister_to_txt(gpl_folder, las_list)

        # gpl_dir_list = os.listdir(gpl_folder)
        # gpl_dir_list.sort()
        # with open (las_list, 'w') as list:
        #     for item in gpl_dir_list:
        #         if ".las" in item.lower():
        #             list.write(os.path.join(gpl_folder, item) + "\n")

        # def lastools_launcher(icer_command, process_name, folder_name, parent_folder, threads):
        #     start_time = time.time()
        #     exe = os.path.split(icer_command[0])[1]
        #     logger("#" * 50 + " " + process_name + " (" + exe + ") Log:\n\n")
        #     output_folder = os.path.join(parent_folder, folder_name)
        #     os.makedirs(output_folder)
        #     icer_command.append("-odir")
        #     icer_command.append(output_folder)
        #     icer_command.append("-cores")
        #     icer_command.append(threads)
        #     icer_stdout, icer_stderr = subprocess.Popen(icer_command, stdout=subprocess.PIPE,
        #                                                 stderr=subprocess.PIPE).communicate()
        #     logger(exe + ' standard output messages:\n\n')
        #     if icer_stdout:
        #         logger(icer_stdout + "\n")
        #     else:
        #         logger("None \n\n")
        #     logger(exe + ' standard error messages:\n\n')
        #     if icer_stderr:
        #         logger(icer_stderr + "\n")
        #     else:
        #         logger("None \n\n")
        #     end_time = time.time()
        #     duration = format(end_time - start_time, '.1f')
        #     logger(process_name + ' took ' + str(duration) + ' seconds\n\n')


        # over_and_diff_qc_folder = os.path.join(gpl_qc_folder, "overlap_and_difference")
        # os.makedirs(over_and_diff_qc_folder)

        ol_icer_command = [lasoverlap_filepath, "-lof", las_list, "-step", "1", "-no_diff", "-drop_extended_class",
                           "47", "129", "139", "173", "183", "-drop_user_data", "3", "-values", "-o",
                           "values_1m.tif"]
        lastools_launcher(ol_icer_command, "Overlap Rasters", "%s_overlap_1m" % mission_name, gpl_qc_folder,
                          threads)

        refracted_ol_ch0_icer_command = [lasoverlap_filepath, "-lof", las_list, "-step", "1", "-no_diff",
                                        "-keep_extended_class", "40", "41", "45", "-keep_user_data", "0",
                                        "-values", "-o", "values_1m.tif"]
        lastools_launcher(refracted_ol_ch0_icer_command, "Rfx Overlap Ch0 Rasters", "%s_overlap_rfx_ch0_1m" % mission_name,
                          gpl_qc_folder, threads)

        refracted_ol_ch1_icer_command = [lasoverlap_filepath, "-lof", las_list, "-step", "1", "-no_diff",
                                     "-keep_extended_class", "40", "41", "45",  "-keep_user_data", "1",
                                     "-values", "-o", "values_1m.tif"]
        lastools_launcher(refracted_ol_ch1_icer_command, "Rfx Overlap Ch1 Rasters", "%s_overlap_rfx_ch1_1m" % mission_name,
                          gpl_qc_folder, threads)

        dz_values_icer_command = [lasoverlap_filepath, "-lof", las_list, "-step", "1", "-no_over", "-last_only",
                                  "-keep_extended_class", "2", "40", "-values", "-otif", "-drop_user_data", "3"]
        lastools_launcher(dz_values_icer_command, "DZ (values) Rasters", "%s_dz_gnd_1m" % mission_name,
                          gpl_qc_folder, threads)

        # stddev_lasts_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "0.5", "-elevation", "-stddev",
        #                              "-last_only", "-fill", "3", "-keep_extended_class", "40", "45", "47", "129", "139",
        #                              "173", "183", "-otif"]
        # lastools_launcher(stddev_lasts_icer_command, "StdDev of Lasts", "%s_stddev_0pt5m" % mission_name,
        #                   surfaces_qc_folder, threads)

        grn_lasts_int_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "1", "-fill", "3",
                                      "-last_only", "-keep_extended_class", "2", "6", "40",
                                      "-drop_user_data", "3", "-intensity", "-average",  "-oasc"]
        lastools_launcher(grn_lasts_int_icer_command, "Green Ground Returns Intensity Raster",
                          "%s_int_grn_2_6_40_0pt5m" % mission_name, gpl_qc_folder, threads)

        grn_firsts_int_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "1", "-fill", "3",
                                      "-first_only", "-drop_extended_class", "7",
                                      "-drop_user_data", "3", "-intensity", "-average",  "-oasc"]
        lastools_launcher(grn_firsts_int_icer_command, "Green First Return Intensity Raster",
                          "%s_int_grn_firsts_0pt5m" % mission_name, gpl_qc_folder, threads)

        nir_firsts_int_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "1", "-first_only",  "-fill", "3",
                                       "-keep_user_data", "3","-keep_class", "1", "2", "9", "-intensity", "-average",
                                       "-oasc"]
        lastools_launcher(nir_firsts_int_icer_command, "NIR First Return Intensity Raster",
                          "%s_int_nir_firsts_0pt5m" % mission_name, gpl_qc_folder, threads)

        ### LasTools version:
        # lasgrid_filepath = os.path.join(lastools_path, "lasgrid.exe")
        # lasoverlap_filepath = os.path.join(lastools_path, "lasoverlap.exe")
        # blast2dem_filepath = os.path.join(lastools_path, "blast2dem.exe")

        # over_and_diff_qc_folder = os.path.join(gpl_qc_folder, "overlap_and_difference")
        # os.makedirs(over_and_diff_qc_folder)
        #
        # overlap_icer_command = [lasoverlap_filepath, "-lof", las_list, "-step", "1", "-no_diff", "drop_extended_class",
        #                         "47", "129", "139", "173", "-drop_user_data", "3", "-values", "-o", "values_1m.tif"]
        # lastools_launcher(overlap_icer_command, "Overlap Rasters", "overlap_1m", over_and_diff_qc_folder, threads)
        #
        # dz_values_icer_command = [lasoverlap_filepath, "-lof", las_list, "-step", "1", "-no_over",
        #                           "-drop_extended_class", "129", "139", "173", "-drop_user_data", "3", "-values",
        #                           "-otif"]
        # lastools_launcher(dz_values_icer_command, "DZ (values) Rasters", "dz_values_1m", over_and_diff_qc_folder, threads)
        #
        # dz_rgb_icer_command = [lasoverlap_filepath, "-lof", las_list, "-step", "1", "-no_over",
        #                        "-drop_extended_class", "129", "139", "173", "-drop_user_data", "3", "-min_diff", "0.06",
        #                        "-max_diff", "0.16", "-otif"]
        # lastools_launcher(dz_rgb_icer_command, "DZ (RGB) Rasters", "dz_rgb_1m", over_and_diff_qc_folder, threads)
        #
        # densities_qc_folder = os.path.join(gpl_qc_folder, "densities")
        # os.makedirs(densities_qc_folder)
        #
        # refracted_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "0.5", "-fill",
        #                           "3",  "-keep_class", "47", "45", "40", "-drop_user_data", "3",
        #                           "-point_density",  "-otif"]
        # lastools_launcher(refracted_icer_command,"Refracted Green Point Density Raster",
        #                   "refracted_0pt5m", densities_qc_folder, threads)
        #
        # unrefracted_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "0.5", "-fill", "3",
        #                             "-drop_extended_class", "47", "45", "40", "173", "-drop_user_data", "3",
        #                             "-point_density",  "-otif"]
        # lastools_launcher(unrefracted_icer_command, "Unrefracted Green Point Density Raster",
        #                   "unrefracted_0pt5m", densities_qc_folder, threads)
        #
        # # bathy_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "0.5", "-fill", "3",
        # #                   "-keep_class", "26", "-point_density",  "-otif"]
        # # lastools_launcher(bathy_icer_command, "Bathy Ground Point Density Raster",
        # #                   "bathy_ground_0pt5m", densities_qc_folder)
        # #
        # # topo_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "0.5", "-fill", "3",
        # #                   "-keep_class", "2", "-point_density",  "-otif"]
        # # lastools_launcher(topo_icer_command, "Topo Ground Point Density Raster",
        # #                   "topo_ground_0pt5m", densities_qc_folder)
        #
        # native_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "10", "-drop_user_data", "3",
        #                        "-keep_class", "1", "2", "-keep_extended_class", "40", "41", "45",
        #                        "-point_density", "-first_only", "-otif"]
        # lastools_launcher(native_icer_command, "Native Density Raster", "native_10m", densities_qc_folder, threads)
        #
        # noise_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "0.5", "-keep_class", "7",
        #                       "-keep_extended_class", "47", "-point_density",  "-otif"]
        # lastools_launcher(noise_icer_command, "Noise Density Raster", "noise_0pt5m", densities_qc_folder, threads)
        #
        # withheld_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "0.5",
        #                          "-keep_extended_class", "173", "129", "139", "-point_density",  "-otif"]
        # lastools_launcher(withheld_icer_command, "Edge and Tail Clip Density Raster", "withheld_0pt5m",
        #                   densities_qc_folder, threads)
        #
        # intensities_qc_folder = os.path.join(gpl_qc_folder, "intensities")
        # os.makedirs(intensities_qc_folder)
        #
        # grn_firsts_int_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "0.5", "-fill", "3","-first_only",
        #                                "-drop_class", "7", "drop_extended_class", "47", "129", "139", "173",
        #                                "-drop_user_data", "3", "-intensity", "-average",  "-oasc"]
        # lastools_launcher(grn_firsts_int_icer_command, "Green First Return Intensity Raster",
        #                   "grn_first_return_0pt5m", intensities_qc_folder, threads)
        #
        # surfaces_qc_folder = os.path.join(gpl_qc_folder, "surfaces")
        # os.makedirs(surfaces_qc_folder)
        #
        # hh_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "0.5", "-fill", "3", "-elevation", "-highest",
        #                 "-drop_extended_class", "129", "139", "173", "-drop_user_data", "3",  "-otif"]
        # lastools_launcher(hh_icer_command, "Higest Hit Rasters", "hh_0pt5m", surfaces_qc_folder, threads)
        #
        # hh_nir_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "0.5", "-fill", "3",
        #                    "-keep_class", "9", "11", "12", "-elevation", "-highest",  "-otif"]
        # lastools_launcher(hh_nir_icer_command, "NIR Highest Hit Rasters", "nir_hh_0pt5m", surfaces_qc_folder, threads)
        #
        # lh_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "0.5", "-fill", "3", "-keep_class", "1", "2",
        #                    "-keep_extended_class", "40", "41", "45", "-elevation", "-lowest",  "-otif"]
        # lastools_launcher(lh_icer_command, "Lowest Hit Rasters", "lh_0pt5m", surfaces_qc_folder, threads)
        #
        # lh_nir_icer_command = [lasgrid_filepath, "-lof", las_list, "-step", "0.5", "-fill", "10",
        #                        "-drop_extended_class", "129", "-drop_user_data", "0", "1", "-drop_class", "14",
        #                        "-elevation", "-lowest",  "-otif"]
        # lastools_launcher(lh_nir_icer_command, "Lowest Hit NIR Rasters", "lh_nir_0pt5m", surfaces_qc_folder, threads)
        #
        # be_icer_command = [blast2dem_filepath, "-lof", las_list, "-step", "0.5", "-keep_class", "2",
        #                    "-keep_extended_class", "40", "-buffered", "10", "-otif"]
        # lastools_launcher(be_icer_command, "DEM Rasters", "be_0pt5m", surfaces_qc_folder, threads)
        #
        # wsm_icer_command = [blast2dem_filepath, "-lof", las_list, "-step", "0.5", "-keep_extended_class", "41",
        #                     "-buffered", "10", "-otif"]
        # lastools_launcher(wsm_icer_command, "WSM Rasters", "wsm_0pt5m", surfaces_qc_folder, threads)
        ### mosaic rasters option

        # shutil.rmtree(tslave_reports_folder)
        # os.makedirs(tslave_reports_folder)

        ### add logging from lastools stdout/stderr

        end_time = time.time()
        duration = format(end_time - start_time, '.1f')
        logger(process_name + " took " + str(duration) + " seconds\n\n")

        print("QC rasters complete (took %s seconds)!\n\n" % duration.rstrip())

        if processing_step == processing_end:
            logger("#" * 50 + " RUN COMPLETE    " + datetime.now().strftime('%Y%m%d_%H%M%S') + " " + "#" * 50 + "\n\n")
            print("RUN COMPLETE " + datetime.now().strftime('%Y%m%d_%H%M%S'))
            mainloop_wrapper(main_frame)
        processing_step = 8

    if processing_step == 8:

        # search tielines

        process_name = "Search Tielines"
        logger("#" * 50 + " " + process_name + " (tslave.exe) Log:\n\n")

        make_temp_tslave_folders(tslave_progress_folder, tslave_reports_folder, tslave_task_folder, main_frame,
                                 "replace")

        print("Searching " + mission_name + " tielines...")
        ## do this better
        block_count = 0
        with open(imported_project, 'r') as project:
            for line in project:
                if "Block " in line:
                    block_count += 1

        search_tielines_macro = os.path.join(reports_folder, "1_NOAA_search_tielines_" + mission_name + ".mac")
        search_tielines_macro_contents = ["[TerraScan macro]\n",
                                          "Version=riegl_ic_launcher\n",
                                          "Description=search tielines\n",
                                          "Author=LH\n",
                                          "ByLine=0\n",
                                          "ByScanner=0\n",
                                          "NeedTrajectories=2\n",
                                          "SlaveCanRun=1\n",
                                          "AnotherComputerCanRun=1\n",
                                          "CanBeDistributed=1\n", "\n",
                                          "FnMatchSearchTie(\"" + os.path.join(tielines_folder,"#block.til")
                                          + "\",\"" + tieline_settings_file + "\")"]

        with open(search_tielines_macro, 'w') as macro:
            for line in search_tielines_macro_contents:
                macro.write(line)

        ## better way to do this??? also include a timeout? - modify when updating start_script
        while True:
            lic = check_terra_licenses()
            if (int(lic['tscan'][:1]) < 2 or int(lic['tslave'][:1]) < 2) and int(lic['tmatch'][:1]) < 2:
                break
            else:
                lic_summary_string = '\n' + '\t' + 'License statuses:\n\n'
                for license in lic:
                    lic_summary_string += '\t' + license + lic[license][1:] + '\n'
                ok = messagebox.askokcancel('TSlave Import Warning', 'Please ensure that there is a '
                                                                       'TerraScan/TerraSlave license and a TerraMatch '
                                                                       'license checked on the local machine.\n'
                                              + lic_summary_string + 'Press ok to continue.')
                if ok:
                    continue
                else:
                    mainloop_wrapper(main_frame)

        tieline_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        start_time = time.time()
        tieline_task_file = os.path.join(tslave_task_folder, tieline_timestamp + ".tsk")

        tieline_task_contents = ["[TerraSlave task]\n",
                                 "Task=tscan_macro\n",
                                 "Macro=" + search_tielines_macro + "\n",
                                 "SaveResults=0\n",
                                 "Neighbours=0.000\n",
                                 "NeedMatch=1\n",
                                 "Dispatcher=" + dispatcher + "\n",
                                 "ProcessBy=" + dispatcher + "\n",
                                 "Project=" + gpl_project + "\n",
                                 "Blocks=1-" + str(block_count) + "\n",
                                 "Trajectories=" + calib_trj_folder + "\n",
                                 "PointClasses=" + terra_ptc_file + "\n",
                                 "Transformations=" + terra_transform_file + "\n",
                                 "Progress=" + tslave_progress_folder + "\n",
                                 "Reports=" + tslave_reports_folder + "\n"]

        tslave_launcher(processing_step, processing_start, processing_end, threads, temp_folder, main_frame)

        with open(tieline_task_file, 'w') as task:
            for line in tieline_task_contents:
                task.write(line)

        while True:
            if os.path.isfile(tieline_task_file):
                time.sleep(30)
            else:
                break

        #tieline_tslave_reports_folder = os.path.join(reports_folder, "1_tslave_tieline_task_reports")
        #os.makedirs(tieline_tslave_reports_folder)

        til_master_log_file = os.path.join(reports_folder, "1_tslave_til_master_report__run_%s.txt" % run_start_time)

        logger(process_name + " error messages:\n\n")
        error_count = 0
        for file in os.listdir(tslave_reports_folder):
            if file.endswith(".txt"):
                til_log_lines_list = []
                with open(os.path.join(tslave_reports_folder,file), 'r') as report:
                    for line in report:
                        if "Block" in line:
                            block_name = line.replace("Block ", "")
                        if "Status=Failed" in line:
                            error_count += 1
                            logger("TerraSlave failed on " + block_name + "\n")
                            with open(os.path.join(reports_folder, "__Refraction_Wrapper_log_TIELINE_ERRORS_RUN_%s.txt"
                                                   % run_start_time), 'a') as error_log:
                                error_log.write("TerraSlave failed on " + block_name)
                            print("Error: TSlave tieline search failed.")
                        if "Status=Aborted" in line:
                            error_count += 1
                            logger("TerraSlave aborted on " + block_name + "\n")
                            with open(os.path.join(reports_folder, "__Refraction_Wrapper_log_TIELINE_ERRORS_RUN_%s.txt"
                                                                   % run_start_time), 'a') as error_log:
                                error_log.write("TerraSlave aborted on " + block_name)
                            print("Error: TSlave tieline search aborted.")
                        til_log_lines_list.append(line)
                with open(til_master_log_file, 'a') as log:
                    for line in til_log_lines_list:
                        log.write(line)
                    log.write("\n\n")

                #shutil.copy2(os.path.join(tslave_reports_folder,file), tieline_tslave_reports_folder)

        if error_count == 0:
            logger("None\n\n")

        tieline_task_file_output = os.path.join(reports_folder, "1_tslave_tieline_search_task_file__run_%s.tsk"
                                                % run_start_time)

        with open(tieline_task_file_output, 'w') as task:
            for line in tieline_task_contents:
                task.write(line)

        # shutil.rmtree(tslave_reports_folder)
        # os.makedirs(tslave_reports_folder)

        end_time = time.time()
        duration = format(end_time - start_time, '.1f')
        logger(process_name + " took " + str(duration) + " seconds\n\n")

        print("Tieline search complete (took %s seconds)!" % duration.rstrip())

        logger("#" * 50 + " RUN COMPLETE    " + datetime.now().strftime('%Y%m%d_%H%M%S') + " " + "#" * 50 + "\n\n")
        print("RUN COMPLETE " + datetime.now().strftime('%Y%m%d_%H%M%S'))
        mainloop_wrapper(main_frame)


def tslave_launcher(processing_step, processing_start, processing_end, threads, temp_folder, main_frame):
    task_list = subprocess.check_output('tasklist', shell=True)
    my_command = os.path.join(temp_folder, "tslave.exe")
    if processing_step == 4:
        os.startfile(my_command)
    if processing_step == 6:
        if processing_start < 5:
            ### change this to a log instead
            if not "tslave.exe" in task_list:
                messagebox.showwarning('TSlave Error',
                                         'TSlave instances crashed after Import step.')
                print('TSlave instances crashed after Import step.')
                print('Process stopped.')
                mainloop_wrapper(main_frame)
            for i in range(int(threads) - 1):
                os.startfile(my_command)
        else:
            for i in range(int(threads)):
                os.startfile(my_command)
    if processing_step  == 7:
        if processing_start < 7:
            if not "tslave.exe" in task_list:
                messagebox.showwarning('TSlave Error',
                                         'TSlave instances crashed after GPCH step')
                print('TSlave instances crashed after GPCH step.')
                print('Process stopped.')
                mainloop_wrapper(main_frame)
        else:
            for i in range(int(threads)):
                os.startfile(my_command)
    if processing_step  == 8:
        if processing_start < 8:
            if not "tslave.exe" in task_list:
                messagebox.showwarning('TSlave Error',
                                         'TSlave instances crashed after Search Tielines step')
                print('TSlave instances crashed after Tielines step.')
                print('Process stopped.')
                mainloop_wrapper(main_frame)
        else:
            for i in range(int(threads)):
                os.startfile(my_command)

def locker(lock_file, email, mission_name, dispatcher):
    try:
        os.close(os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        timenow = datetime.now().strftime('%Y%m%d_%H%M%S')
        with open(lock_file, 'w') as lock:
            lock.write('Lock created by %s on %s while processing mission %s at datetime %s'
                       % (email.split('@')[0], dispatcher, mission_name, timenow))
    except OSError as e:
        if e.errno == errno.EEXIST:  # System is already locked as the file already exists.
            return "trajectories locked"
        else:  # Something unexpected went wrong so reraise the exception.
            raise
    return "lock created"  # System has successfully been locked by the function

def check_terra_licenses():
    license_folder = r'C:\terra64\license'
    ### do this better!
    apps_to_check = ['tscan', 'tslave', 'tmatch']
    license_status = {}
    for app in apps_to_check:
        license_file = os.path.join(license_folder, app + '.lic')
        if os.path.isfile(license_file):
            with open(license_file, 'r') as lic:
                lic_timevalid = None
                for line in lic:
                    if 'ValidUntil=' in line:
                        lic_validuntil = line[-11:].rstrip() + '.23.59.59'
                        lic_validuntil_formatted = datetime.strptime(lic_validuntil, '%d.%m.%Y.%H.%M.%S')
                        lic_timevalid = (lic_validuntil_formatted - datetime.now()).total_seconds()
            if lic_timevalid:
                if lic_timevalid > 0:
                    lic_hoursvalid = int(round(lic_timevalid/3600))
                    if lic_hoursvalid >= 24:
                        status_text = '0.lic is valid'
                    else:
                        status_text = '1.lic expires within 24hr'
                else:
                    status_text = '2.lic is expired'
            else:
                status_text = '4.lic is incorrectly formatted'
        else:
            status_text = '3.lic is not checked out'
        license_status[app] = status_text
    return license_status


def rename_swaths_recursively(folder, main_frame):
    flist = []
    xtension = [".las", ".qpx"]

    ### old non-recursive version
    # for item in os.listdir(folder):
    #     if os.path.splitext(item.lower())[1] in xtension:
    #         flist.append(os.path.join(folder, item))  # + "\n")

    for rootdir, directories, items in os.walk(folder):
        for item in items:
            if os.path.splitext(item.lower())[1] in xtension:
                flist.append(os.path.join(rootdir,item))

    for item in flist:

        f = os.path.basename(item)
        p = os.path.dirname(item)

        if re.search('[0-9]{6}_[0-9]{6}_channel_(g_[0-1]|ir).(las|qpx)', f.lower()):
            pass

        else:

            split = f.split()
            ext = os.path.splitext(f)[1]

            try:
                record = split[5].lower()
                # part = record.split('_')
            except IndexError:
                record = 'null'
                messagebox.showwarning('Input Validation Warning',
                                         'LAS files do not have the expected naming scheme.')
                mainloop_wrapper(main_frame)

            if 'channel_g' in record or 'channel_ir' in record:
                fnew = record + ext
                os.rename(item, os.path.join(p, fnew))
            else:
                messagebox.showwarning('Input Validation Warning',
                                         'LAS files do not have the expected naming scheme.')
                mainloop_wrapper(main_frame)


def create_list_of_lists_of_incremental_las(input_list):
    las_list = []
    sorted_list = []
    match_found = False
    for item in input_list:
        if item.lower().endswith(".las"):
            las_list.append(item)
    las_list.sort()
    for las_file in las_list:
        swath_name = os.path.basename(las_file).rsplit("[")[0]
        for swath_paths in sorted_list:
            match_found = False
            sorted_swath_name = os.path.basename(swath_paths[0]).rsplit("[")[0]
            if swath_name == sorted_swath_name:
                swath_paths.append(las_file)
                match_found = True
        if match_found:
            pass
        else:
            new_swath = [las_file]
            sorted_list.append(new_swath)
    return sorted_list

def file_lister(root_folder, str_filt_list=None, ext_filt_list=None, recursive=False):
    file_list = []
    if recursive:
        for rootdir, dirs, items in os.walk(root_folder):
            for item in items:
                file_list.append(os.path.join(rootdir, item))
    else:
        folder_contents = os.listdir(root_folder)
        for item in folder_contents:
            file_list.append(os.path.join(root_folder, item))
    file_list.sort()
    if ext_filt_list:
        filtered_file_list = []
        for item in file_list:
            for ext in ext_filt_list:
                if item.lower().endswith(ext.lower()):
                    filtered_file_list.append(item)
        file_list=filtered_file_list
    if str_filt_list:
        filtered_file_list, unmatched_filters = filter_list_by_list_of_strings(file_list, str_filt_list)
        file_list=filtered_file_list
    return file_list

def filter_list_by_list_of_strings(input_list, string_filter_list, array=False):
    filtered_file_list = []
    filters_not_found_list = []
    for string in string_filter_list:
        match_found = False
        for item in input_list:
            if array:
                if string.lower() in os.path.basename(item[0]).split('[')[0].lower():
                    filtered_file_list.append(item)
                    match_found = True
            else:
                if string.lower() in os.path.basename(item).lower():
                    filtered_file_list.append(item)
                    match_found = True
        if not match_found:
            filters_not_found_list.append(string)
    return filtered_file_list, filters_not_found_list


def file_lister_to_txt(input_folder, output_filepath):
    dir_list = os.listdir(input_folder)
    if not output_filepath.rsplit(".")[1] == "txt":
        return "file_lister error: output_filepath must have a TXT extension"
    dir_list.sort()
    with open(output_filepath, 'w') as list:
        for item in dir_list:
            if ".las" in item.lower():
                list.write(os.path.join(input_folder, item) + "\n")

def ren_ptsrcid_to_timestamp(input_folder, ref_folder, trj_folder, main_frame):

    max_trj_buffer = 6 #seconds

    list_of_las = file_lister(input_folder, ext_filt_list=['.las'])
    list_of_reference_items = file_lister(ref_folder, ext_filt_list=['.las'])
    list_of_trj = file_lister(trj_folder, ext_filt_list=['.trj'], recursive=True)
    list_of_las_to_rename = []
    trj_dict = {}


    for item in list_of_las:
        swath = re.search('^(\d{6}_\d{6})_channel_((g_\d)|(ir))(\[\d{3}\])?\.las', os.path.basename(item).lower())
        if swath or 'upland' in item.lower():
            pass
        else:
            list_of_las_to_rename.append(item)

    if list_of_las_to_rename:
        print('Renaming input las files to match Riegl convention...')
        for trj in list_of_trj:
            try:
                trj_name = re.search('^SN\d{4}_(\w{3}_)?(\d{8}_\d{6})_(\d{1,5})_?(\d{3,5})?\.trj', os.path.basename(trj))
                timestamp = trj_name.group(2)
                ptsrcid = ''
                if trj_name.group(4):
                    ptsrcid = trj_name.group(4)
                else:
                    ptsrcid = trj_name.group(3)
                trj_dict.update({str(ptsrcid): timestamp})
            except Exception as e:
                print('unable to match trajectory name to swaths: ', e , trj)
                pass

        id_dict = {}
        for ptsrcid, timestamp in trj_dict.items():
            trj_timestamp = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            for item in list_of_reference_items:
                try:
                    swath = re.search('^(\d{6}_\d{6})_channel_((g_\d)|(ir))(\[\d{3}\])?\.las', os.path.basename(item).lower())
                    swath_time_string = swath.group(1)
                    swath_timestamp = datetime.strptime(swath_time_string, "%y%m%d_%H%M%S")
                    swath_timestamp_string = datetime.strftime(swath_timestamp, "%y%m%d_%H%M%S")
                    delta = int(abs(trj_timestamp - swath_timestamp).total_seconds())
                    if delta <= int(max_trj_buffer):
                        id_dict.update({str(ptsrcid): swath_time_string})
                except Exception as e:
                    print('failure to find timestamp: ', e, item)
                    pass

        renamed_counter = 0
        for item in list_of_las:
            swath = re.search('^(\d{5})\w*?.las', os.path.basename(item).lower())
            if swath:
                try:
                    item_name = swath.group(0)
                    item_ptsrcid = swath.group(1).lstrip('0')
                    if any(x in item_name for x in ['ch0', 'ch_0', 'g_0', 'g0']):
                        item_channel = 'G_0'
                    elif any(x in item_name for x in ['ch1', 'ch_1', 'g_1', 'g1']):
                        item_channel = 'G_1'
                    elif any(x in item_name for x in ['ch3', 'ch_3', 'ir3', 'ir_3', 'chir', 'ch_ir',' chnir', 'ch_nir', 'ir', 'nir']):
                        item_channel = 'IR'
                    else:
                        continue
                    timestamp = id_dict[item_ptsrcid]
                    new_item_name = '%s_Channel_%s.las' % (timestamp, item_channel)
                    new_item = os.path.join(os.path.dirname(item), new_item_name)
                    os.rename(item, new_item)
                    renamed_counter +=1
                except OSError:
                    print('unable to rename %s ' % item)
                except Exception as e:
                    print('failure to rename: ', e, item)
                    messagebox.showwarning('Error',
                                           'Unexpected naming of swaths in %s.\n'
                                           'Expects either yymmdd_HHMMSS_Channel_<channelID> or\n'
                                           '#####_<channelID>.' % input_folder)
                    mainloop_wrapper(main_frame)
                    pass
        return renamed_counter

def folder_maker(directory, main_frame, mode):
    if mode in ["skip"]:
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except OSError:
                if not os.path.isdir(directory):
                    folder_path, folder_name = os.path.split(directory)
                    messagebox.showwarning('Error',
                                             'Unable to create ' + folder_name + 'folder in ' + folder_path + '.')
                    print('Unable to create ' + folder_name + 'folder in ' + folder_path + '.')
                    print('Process stopped.')
                    mainloop_wrapper(main_frame)
            else:
                print('... folder already exists, skipped creating %s ...' % directory)
    elif mode in ["replace", "overwrite", "clear"]:
        try:
            if os.path.isdir(directory):
                shutil.rmtree(directory)
                time.sleep(5)
            os.makedirs(directory)
        except OSError:
            if not os.path.isdir(directory):
                folder_path, folder_name = os.path.split(directory)
                messagebox.showwarning('Error',
                                         'Unable to replace ' + folder_name + ' folder in ' + folder_path + '.')
                print('Unable to create ' + folder_name + 'folder in ' + folder_path + '.')
                print('Process stopped.')
                mainloop_wrapper(main_frame)
    else:
        return "Error in folder_maker function: mode not recognized."

def make_temp_tslave_folders(tslave_progress_folder, tslave_reports_folder, tslave_task_folder, main_frame, mode):
    folder_maker(tslave_task_folder, main_frame, mode)
    folder_maker(tslave_progress_folder, main_frame, mode)
    folder_maker(tslave_reports_folder, main_frame, mode)

def browser(mode, browse_entry, type):

    if mode == 'Folder':
        # read the contents of the folder entry widget
        input_folder = browse_entry.get()

        # set the initial browse directory based on those contents if possible
        if os.path.isdir(input_folder):
            initial_dir = input_folder
        elif os.path.isfile(input_folder):
            initial_dir = os.path.dirname(os.path.abspath(input_folder))
        else:
            initial_dir = os.path.expanduser('~')

        # open browse dialog & set input_folder if valid directory is chosen, updating entry widget
        input_folder = askdirectory(mustexist=1, initialdir=initial_dir)
        if os.path.isdir(input_folder):
            input_folder = input_folder.replace('/', '\\').strip()
            browse_entry.delete(0, END)
            browse_entry.insert(0, input_folder)

    elif mode == 'File':
        # start with whatever is currently in the macro file entry widget
        file_name = browse_entry.get()

        # if the macro file entry widget contains a file path, open the browse window to that file's folder
        if os.path.isfile(file_name):
            initial_dir = os.path.dirname(os.path.abspath(file_name))
        # if the macro file entry widget contains a folder path, open the browse window to that location
        elif os.path.isdir(file_name):
            initial_dir = file_name
        # otherwise, open the browse window to the script location
        else:
            initial_dir = os.path.expanduser('~')

        ### make filemask a parameter
        if type == 'shape':
            filemask = [("shapefiles", "*.shp")]
        elif type == 'settings':
            filemask = [("settings", "*.settings")]
        # open the askopenfilename widget
        file_name = askopenfilename(initialdir=initial_dir, filetypes=filemask)
        file_name = file_name.replace('/', '\\').strip()
        browse_entry.delete(0, END)
        # if the user selects a valid file, populate the folder entry widget
        if os.path.isfile(file_name):
            browse_entry.insert(0, file_name)

def batch_commands(subprocess_command_list, threads):
    command_index = 0
    batches = -(-len(subprocess_command_list) // int(
        threads))  # using negative signs and integer division to round up
    batch_list = []
    for i in range(batches):
        for j in range(int(threads)):
            barrel = []
            if command_index >= len(subprocess_command_list):
                break
            # launch an instance
            command = subprocess.Popen(subprocess_command_list[command_index])
            batch_list.append(command)
            command_index += 1

        for command in batch_list:
            command.wait()

def get_refraction_xml_steps(sensor, swath, obj_list, riegl_str_dict, shp_dict, surfaces, ws_list, grn_trj_dir,
                             attenuation_coeff_dict, int_norm_dict):
    def get_refraction_step(obj_path, shp_path, attenuation_coeff, grn_trj_dir):
        refraction_step = """<ReclassShp v="2.3.3">
            <ShpPath>%s</ShpPath>
            <KeepInside>1</KeepInside>
            <Class1>1N, 129N</Class1>
            <Class2>101N, 229N</Class2>
            <Slice>250</Slice>
        </ReclassShp>
        <Refract v="2.0.0">
            <SurfType>OBJFILE</SurfType>
            <SurfPath>%s</SurfPath>
            <ExpandSearch do="1">999.99</ExpandSearch>
            <TrajPath>%s</TrajPath>
            <RefractAir>1.000280</RefractAir>
            <RefractWater>1.333000</RefractWater>
            <RefractClass>101N, 229N</RefractClass>
            <PostRefractClass do="1">45N, 173N</PostRefractClass>
            <MinDepth>
                <Depth>0.050</Depth>
                <ShallowClass do="0">41N</ShallowClass>
            </MinDepth>
            <BiasCorr>%s</BiasCorr>
            <ExtraBytes>RefDepth IncidenceAng BathyFlags</ExtraBytes>
            <Simulate>0</Simulate>
        </Refract>
        <LogicTransfer v="2.2.0">
            <RefLas v="2.2.0">
                <RefPath></RefPath>
                <MatchMode>RM_FILEORDER</MatchMode>
                <RefChan do="0">
                    <AssignChan v="2.0.0">
                        <Source>2</Source>
                        <UniformChan>1</UniformChan>
                        <Offset do="0">-1</Offset>
                        <Remap>0 1 2 3</Remap>
                    </AssignChan>
                </RefChan>
            </RefLas>
            <Logic>
                <Rule>
                    <InputA>0 0 0 101N</InputA>
                    <InputB>0 0 5 0A</InputB>
                    <Output>6 1N</Output>
                </Rule>
                <Rule>
                    <InputA>0 0 0 229N</InputA>
                    <InputB>0 0 5 0A</InputB>
                    <Output>6 129N</Output>
                </Rule>
            </Logic>
        </LogicTransfer>""" % (shp_path, obj_path, grn_trj_dir, attenuation_coeff)
        return refraction_step
    def get_int_steps(int_norm_dict, sensor):
        int_steps ="""<NormalizeInt v="2.0.0">
            <Format>CLIP16BIT</Format>
            <Inverse>0</Inverse>
            <Profiles>
                <Profile default="1">
                    <TrajPath></TrajPath>
                    <ReScale do="0">
                        <ModeExtended>MULTONE</ModeExtended>
                        <Scales>1.000,1.000,1.000,1.000,1.000</Scales>
                    </ReScale>
                    <Atmos do="0">
                        <Trans>1.00</Trans>
                        <Range>900</Range>
                    </Atmos>
                    <AutoGain do="0">
                        <Path></Path>
                    </AutoGain>
                    <Power do="0">
                        <RefPower>0.000000</RefPower>
                        <LogPath></LogPath>
                        <WeekPath></WeekPath>
                    </Power>
                    <ScanAngle do="0">
                        <AngCorr>INCIDENCE</AngCorr>
                        <AngSource>SCANNER</AngSource>
                        <AngleValues>1.00,1.00,1.00,1.00</AngleValues>
                        <AngleSync>1</AngleSync>
                    </ScanAngle>
                    <Depth do="1">
                        <WaterClasses>45N, 173N</WaterClasses>
                        <AttName>refracted depth</AttName>
                        <SlopeCorr>%s</SlopeCorr>
                        <OffsetCorr>%s</OffsetCorr>
                    </Depth>
                </Profile>
            </Profiles>
        </NormalizeInt>
        <ReclassInt v="2.0.0">
            <FromClass do="0">45N</FromClass>
            <ToClass>26N</ToClass>
            <IntFilter>PEAK</IntFilter>
            <IntMin>0</IntMin>
            <IntMax>255</IntMax>
            <PeakEcho>3</PeakEcho>
            <PeakMin>3.00</PeakMin>
            <AfterPeak do="1">24N</AfterPeak>
        </ReclassInt>
        <ReclassInt v="2.0.0">
            <FromClass do="0">1N</FromClass>
            <ToClass>32N</ToClass>
            <IntFilter>PEAK</IntFilter>
            <IntMin>0</IntMin>
            <IntMax>255</IntMax>
            <PeakEcho>2</PeakEcho>
            <PeakMin>5.00</PeakMin>
            <AfterPeak do="1">37N</AfterPeak>
        </ReclassInt>""" % (int_norm_dict[sensor][0], int_norm_dict[sensor][1])
        return int_steps
    refraction_steps = ''
    swathname = os.path.basename(swath).lower()
    attenuation_coeff = attenuation_coeff_dict[sensor]
    if riegl_str_dict['grn'] in swathname:
        ###TODO determine whether this approach (each step independent) will fulfill requirements
        if surfaces[2] in ws_list:
            shape_path = shp_dict[surfaces[2]]
            obj_path = ''
            for item in obj_list:
                if riegl_str_dict[surfaces[2]] in item.lower():
                    obj_path = item
            if obj_path:
                step = get_refraction_step(obj_path, shape_path, attenuation_coeff, grn_trj_dir)
            else:
                print('no %s obj for swath %s' % (surfaces[2], swathname))
            refraction_steps += step
        if surfaces[0] in ws_list:
            shape_path = shp_dict[surfaces[0]]
            obj_path = ''
            step = ''
            if riegl_str_dict['ch0'] in swathname:
                for item in obj_list:
                    if riegl_str_dict['ch0'] in item.lower():
                        obj_path = item
            if riegl_str_dict['ch1'] in swathname:
                for item in obj_list:
                    if riegl_str_dict['ch1'] in item.lower():
                        obj_path = item
            if obj_path:
                step = get_refraction_step(obj_path, shape_path, attenuation_coeff, grn_trj_dir)
            else:
                print('no %s obj for swath %s' % (surfaces[0], swathname))
            refraction_steps += step
        if surfaces[1] in ws_list:
            shape_path = shp_dict[surfaces[1]]
            obj_path = ''
            step = ''
            for item in obj_list:
                if riegl_str_dict[surfaces[1]] in item.lower():
                    obj_path = item
            if obj_path:
                step = get_refraction_step(obj_path, shape_path, attenuation_coeff, grn_trj_dir)
            else:
                print('no %s obj for swath %s' % (surfaces[1], swathname))
            refraction_steps += step

        refraction_steps += get_int_steps(int_norm_dict, sensor)
    elif riegl_str_dict['nir'] in swathname:
        pass
    else:
        print('Unexpected swath type input %s' % swath)
    return refraction_steps

def get_xml(dispatcher, refraction_steps, ws_las_folder):
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <!--Written by %s v%s at %s from %s-->
    <LasMonkeyConfig v="2.0" taskid="190517-083834">
        <InPath></InPath>
        <OutPath></OutPath>
        <MaxThreads>1</MaxThreads>
        <InputDir v="2.0.0">
            <Recursive>0</Recursive>
            <WaveImport>0</WaveImport>
            <FullClass>0</FullClass>
            <Unsplit do="0">^(.*)[a-d]\.la[sz]$</Unsplit>
            <LoadIncrement>15</LoadIncrement>
            <Buff help="0" all="0">0</Buff>
            <InMask>
                <Type>IM_NONE</Type>
                <UseLas>1</UseLas>
                <UseLaz>1</UseLaz>
                <ListPath></ListPath>
                <ListAtt></ListAtt>
                <ResumeExt>*.las</ResumeExt>
                <Expression></Expression>
            </InMask>
        </InputDir>
        <LogicTransfer v="2.2.0">
            <RefLas v="2.2.0">
                <RefPath></RefPath>
                <MatchMode>RM_FILEORDER</MatchMode>
                <RefChan do="0">
                    <AssignChan v="2.0.0">
                        <Source>2</Source>
                        <UniformChan>1</UniformChan>
                        <Offset do="0">-1</Offset>
                        <Remap>0 1 2 3</Remap>
                    </AssignChan>
                </RefChan>
            </RefLas>
            <Logic>
                <Rule>
                    <InputA>0 0 0 2N</InputA>
                    <InputB>0 0 5 0A</InputB>
                    <Output>6 1N</Output>
                </Rule>
                <Rule>
                    <InputA>0 0 0 9N</InputA>
                    <InputB>0 0 5 0A</InputB>
                    <Output>6 1N</Output>
                </Rule>
            </Logic>
        </LogicTransfer>%s
        <LogicTransfer v="2.2.0">
            <RefLas v="2.2.0">
                <RefPath>%s</RefPath>
                <MatchMode>RM_FILENAME_LOOSE</MatchMode>
                <RefChan do="1">
                    <AssignChan v="2.0.0">
                        <Source>2</Source>
                        <UniformChan>1</UniformChan>
                        <Offset do="0">-1</Offset>
                        <Remap>0 1 2 3</Remap>
                    </AssignChan>
                </RefChan>
            </RefLas>
            <Logic>
                <Rule>
                    <InputA>0 0 0 1N</InputA>
                    <InputB>0 0 5 0A</InputB>
                    <Output>8 0A</Output>
                </Rule>
            </Logic>
        </LogicTransfer>
        <OutLas v="2.0.0">
            <OutputSettings v="2.0.0">
                <KeepFolders>0</KeepFolders>
                <OutPath></OutPath>
                <OutSuppress>0</OutSuppress>
                <OutCaps>RETAIN</OutCaps>
                <OutEcho>268435455</OutEcho>
                <OutClass></OutClass>
            </OutputSettings>
            <LasSettings>
                <OutVersion>99</OutVersion>
                <OutPtFormat>99</OutPtFormat>
                <CompressToLaz>0</CompressToLaz>
                <Greedy>0</Greedy>
                <WriteIndex>0</WriteIndex>
                <WaveExport>NONE</WaveExport>
            </LasSettings>
            <NewHeader do="0">
                <SystemID>Quantum Spatial</SystemID>
                <SoftwareID>LasMonkey 2.4.6</SoftwareID>
                <CreationDate>2019-05-16</CreationDate>
                <ProjectID>0,0,0,</ProjectID>
                <FileSourceID psid="0">0</FileSourceID>
                <ProjVlr>
                    <Method>NONE</Method>
                    <CopyPath></CopyPath>
                    <HDatum>NAD83</HDatum>
                    <HSystem>UTM North</HSystem>
                    <HZone>Zone 10N</HZone>
                    <HUnits>Meters</HUnits>
                    <VDatum>NAVD88</VDatum>
                    <VUnits>Meters</VUnits>
                    <Desc>UTM Zone 10N - Meters</Desc>
                </ProjVlr>
            </NewHeader>
        </OutLas>
    </LasMonkeyConfig>""" % (title, version, time, dispatcher, refraction_steps, ws_las_folder)
    return xml.replace('\\', '/')

def incremental_las_merger(incremental_files_list, output_folder, lasmerge_filepath, threads):
    lasmerge_command_list = []
    list_of_recovered_las = []
    list_counter = 0
    for list in incremental_files_list:
        output_name = os.path.basename(list[0].rsplit("[")[0]).replace('.las','')
        output_file = os.path.join(output_folder, output_name + '.las')
        list_filepath = os.path.join(output_folder, '__incremental_las_list_%s_%s.txt' % (list_counter, output_name))  # "__incremental_las_list_" + str(list_counter) + "_" + output_name + ".txt")
        with open(list_filepath, 'w') as las_list:
            for item in list:
                las_list.write(item + "\n")
        list_of_recovered_las.append(output_file)
        lasmerge_command = [lasmerge_filepath, "-lof", list_filepath, "-o", output_file]
        lasmerge_command_list.append(lasmerge_command)
        list_counter += 1
    batch_commands(lasmerge_command_list, threads)

def match_riegl_swath_names_between_scanners(input_swath, match_swath_list, minimum_time_gap, array=False):
    if array:
        swath_time = datetime.strptime(os.path.basename(input_swath[0])[0:13], "%y%m%d_%H%M%S")
    else:
        swath_time = datetime.strptime(os.path.basename(input_swath)[0:13], "%y%m%d_%H%M%S")
    matches = []
    for item in match_swath_list:
        if array:
            match_time = datetime.strptime(os.path.basename(item[0])[0:13], "%y%m%d_%H%M%S")
        else:
            match_time = datetime.strptime(os.path.basename(item)[0:13], "%y%m%d_%H%M%S")
        delta = int(abs(match_time - swath_time).total_seconds())
        if delta <= int(minimum_time_gap):
            matches.append(item)
    return matches

def read_las_header():
    print('reading las file')
# def run_subprocess(command):
#     ### fix stdout parsing
#     s = subprocess.Popen(command,shell=False, stdout=subprocess.PIPE)
#     stdout = []
#     line = True
#     while line:
#         line = s.stdout.readline()
#         stdout.append(line + '\n')
#         print line
#     return stdout

def mainloop_wrapper(main_frame):
    main_frame.mainloop()
    try:
        main_frame.destroy()
    except TclError:
        pass
    sys.exit()

gui()