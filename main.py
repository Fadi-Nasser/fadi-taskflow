# Fadi TaskFlow - Mobile Version (Simplified & Cleaned)

import flet as ft
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import datetime
import asyncio
import pygame
from functools import partial

SHEET_ID = "1w2oFVgKfE6mHIeSAHHqYYfHTEk2yF4HvTgEpmKQNlQo"
SHEET_NAME = "Sheet1"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

PRIORITY_COLORS = {
    "Very Important": ft.Colors.RED,
    "Important": ft.Colors.AMBER,
    "Less Important": ft.Colors.GREEN_400
}

note_dialog = None
note_field = None
note_task_index = 0

def read_tasks():
    records = sheet.get_all_records()
    return pd.DataFrame(records)

def add_task_to_sheet(task, date, priority):
    now_time = datetime.datetime.now().strftime("%H:%M:%S")
    sheet.insert_row([task, date, "Not Done", priority, now_time, ""], 2)

def update_task_status(index, new_status):
    sheet.update_cell(index + 2, 3, new_status)

def update_task_note(index, note):
    sheet.update_cell(index + 2, 6, note)

def delete_task(index):
    sheet.delete_rows(index + 2)

def play_sound(sound_type="done"):
    try:
        pygame.mixer.init()
        sound_file = "ding.wav" if sound_type == "done" else "ding2.wav"
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play()
    except:
        pass

def main(page: ft.Page):
    page.title = "Fadi TaskFlow - Mobile"
    page.scroll = "auto"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10

    def get_current_time():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    clock_text = ft.Text(get_current_time(), size=13, color=ft.Colors.GREY_500)

    async def update_clock():
        while True:
            clock_text.value = get_current_time()
            page.update()
            await asyncio.sleep(1)

    note_dialog = ft.AlertDialog(modal=True)
    note_field = ft.TextField(label="Your Notes", multiline=True, min_lines=3, max_lines=5, width=400)
    note_task_index = 0

    def open_note_popup(task_name, index, existing_note):
        nonlocal note_task_index
        note_task_index = index
        note_field.value = existing_note
        note_dialog.title = ft.Text(f"📝 Notes for: {task_name}")
        note_dialog.content = note_field
        note_dialog.actions = [
            ft.TextButton("Save", on_click=lambda e: save_note()),
            ft.TextButton("Close", on_click=lambda e: close_note_popup())
        ]
        note_dialog.open = True
        page.dialog = note_dialog
        page.update()

    def save_note():
        update_task_note(note_task_index, note_field.value)
        close_note_popup()

    def close_note_popup():
        note_dialog.open = False
        page.update()

    today_str = datetime.datetime.now().strftime("%Y-%m-%d")

    task_input = ft.TextField(label="Task Name", width=page.width, bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.GREY_800))
    date_input = ft.TextField(label="Date (YYYY-MM-DD)", value=today_str, width=page.width, bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.GREY_800))

    selected_priority = ft.Ref[ft.RadioGroup]()
    priority_select = ft.RadioGroup(
        ref=selected_priority,
        value="Less Important",
        content=ft.Row([
            ft.Radio(value="Very Important", label="🔴"),
            ft.Radio(value="Important", label="🟡"),
            ft.Radio(value="Less Important", label="🟢"),
        ], alignment=ft.MainAxisAlignment.CENTER)
    )

    task_list_column_pending = ft.Column(spacing=10)
    task_list_column_done = ft.Column(spacing=10)
    stats_text = ft.Text("", size=14, color=ft.Colors.GREY_400)

    filter_date = ft.TextField(
        label="Filter by date (YYYY-MM-DD)",
        value=today_str,
        text_size=13,
        height=36,
        border_radius=8,
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.GREY_700),
        border_color=ft.Colors.GREY_500,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=6),
        on_change=lambda e: page.run_task(refresh_tasks)
    )

    dialog = ft.AlertDialog(modal=True)

    def show_popup(message):
        dialog.title = ft.Text("🔔 Notification")
        dialog.content = ft.Text(message)
        dialog.actions = [ft.TextButton("تمام", on_click=lambda e: close_popup())]
        dialog.open = True
        page.dialog = dialog
        page.update()

    def close_popup():
        dialog.open = False
        page.update()

    def toggle_status(index, current_status):
        new_status = "Done" if current_status == "Not Done" else "Not Done"
        update_task_status(index, new_status)
        page.run_task(refresh_tasks)
        if new_status == "Done":
            play_sound()

    def handle_delete(index):
        delete_task(index)
        page.run_task(refresh_tasks)

    def create_hover_handler(container):
        def handle_hover(e):
            container.bgcolor = ft.Colors.GREY_800 if e.data == "true" else ft.Colors.GREY_900
            page.update()
        return handle_hover

    async def refresh_tasks():
        task_list_column_pending.controls.clear()
        task_list_column_done.controls.clear()
        df = read_tasks()
        selected = filter_date.value.strip()
        if selected:
            df = df[df['Date'] == selected]

        df = df[::-1]

        total_tasks = len(df)
        done_tasks = len(df[df["Status"] == "Done"])
        stats_text.value = f"🔢 Total: {total_tasks} | ✅ Done: {done_tasks} | ⏳ Pending: {total_tasks - done_tasks}"

        for index, row in df.iterrows():
            color = PRIORITY_COLORS.get(row.get("Priority", ""), ft.Colors.GREY_700)
            time_display = f"🕒 {row['Time']}" if 'Time' in row else ""
            note = row.get("Note", "")

            task_card = ft.Container(
                bgcolor=ft.Colors.GREY_900,
                border_radius=10,
                padding=10,
                border=ft.border.all(1, ft.Colors.GREY_800),
                animate=ft.animation.Animation(300, "easeInOut"),
                content=ft.Row([
                    ft.Checkbox(value=(row["Status"] == "Done"),
                                on_change=lambda e, i=index, s=row["Status"]: toggle_status(i, s)),
                    ft.Column([
                        ft.Text(row["Task"], size=15, weight=ft.FontWeight.BOLD),
                        ft.Text(f"📅 {row['Date']}  {time_display}", size=13, color=ft.Colors.GREY_500),
                    ], expand=True),
                    ft.Container(width=6, height=30, bgcolor=color, border_radius=4),
                    ft.IconButton(icon=ft.Icons.NOTE, icon_color=ft.Colors.BLUE_200, tooltip="Notes", on_click=lambda e, i=index, t=row["Task"], n=note: open_note_popup(t, i, n)),
                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_300, tooltip="Delete", on_click=lambda e, i=index: handle_delete(i))
                ])
            )
            task_card.on_hover = create_hover_handler(task_card)
            if row["Status"] == "Done":
                task_list_column_done.controls.insert(0, task_card)
            else:
                task_list_column_pending.controls.insert(0, task_card)

        page.update()

    def add_task(e):
        if not task_input.value.strip():
            return
        task_name = task_input.value.strip()
        task_date = date_input.value.strip()
        priority = selected_priority.current.value
        if not task_date:
            task_date = today_str
        add_task_to_sheet(task_name, task_date, priority)
        play_sound("add")
        show_popup("🎉 Task added successfully!")
        task_input.value = ""
        date_input.value = today_str
        selected_priority.current.value = "Less Important"
        page.run_task(refresh_tasks)

    page.add(
        ft.Column([
            ft.Row([
                ft.Text("📲 Fadi TaskFlow", size=22, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                clock_text
            ]),
            stats_text,
            task_input,
            date_input,
            priority_select,
            ft.Container(height=10),
            ft.ElevatedButton("Add Task", icon=ft.Icons.ADD, height=48,
                              style=ft.ButtonStyle(
                                  shape=ft.RoundedRectangleBorder(radius=10),
                                  side=ft.BorderSide(1, ft.Colors.BLUE_GREY_200),
                                  bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE_200),
                                  padding=10
                              ),
                              on_click=add_task),
            ft.Divider(),
            ft.Row([
                ft.Text("🟢 Tasks", size=18, weight=ft.FontWeight.W_600),
                ft.Container(expand=True),
                filter_date
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            task_list_column_pending,
            ft.Divider(height=1, color=ft.Colors.GREY_600),
            ft.Text("✅ Completed", size=16, color=ft.Colors.GREY_500),
            task_list_column_done
        ])
    )

    page.run_task(update_clock)
    page.run_task(refresh_tasks)

ft.app(target=main)
