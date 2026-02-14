import time
import logging
from types import SimpleNamespace
import threading

logger = logging.getLogger(__name__)
event_logger = logging.getLogger('UI.events')

def setup_global_bindings(gui, debug_path):
    try:
        def _global_click(e):
            try:
                with open(debug_path, 'a') as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} GLOBAL CLICK widget={str(e.widget)} x={getattr(e,'x_root',None)} y={getattr(e,'y_root',None)} type={getattr(e,'type',None)} focus={str(gui.root.focus_get())}\n")
            except Exception:
                pass
            try:
                if hasattr(gui, 'canvas') and gui.canvas.winfo_ismapped():
                    cx = e.x_root - gui.canvas.winfo_rootx()
                    cy = e.y_root - gui.canvas.winfo_rooty()
                    if 0 <= cx < gui.canvas.winfo_width() and 0 <= cy < gui.canvas.winfo_height():
                        dot = gui.canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill='red', outline='')
                        gui.root.after(200, lambda: gui.canvas.delete(dot))
            except Exception:
                pass

        def _global_release_forward(e):
            try:
                if hasattr(gui, 'canvas') and gui.canvas.winfo_ismapped():
                    wx = getattr(e, 'x_root', None)
                    wy = getattr(e, 'y_root', None)
                    if wx is None or wy is None:
                        return
                    cx = wx - gui.canvas.winfo_rootx()
                    cy = wy - gui.canvas.winfo_rooty()
                    if 0 <= cx < gui.canvas.winfo_width() and 0 <= cy < gui.canvas.winfo_height():
                        try:
                            event_logger.info('Forwarding global release to canvas at %s,%s', cx, cy)
                        except Exception:
                            pass
                        fake = SimpleNamespace(x=int(cx), y=int(cy), widget=gui.canvas, x_root=wx, y_root=wy)
                        try:
                            gui._on_canvas_release(fake)
                        except Exception:
                            pass
            except Exception:
                pass

        # Also forward global presses into the canvas when they occur inside it
        def _global_press_forward(e):
            try:
                if hasattr(gui, 'canvas') and gui.canvas.winfo_ismapped():
                    wx = getattr(e, 'x_root', None)
                    wy = getattr(e, 'y_root', None)
                    if wx is None or wy is None:
                        return
                    cx = wx - gui.canvas.winfo_rootx()
                    cy = wy - gui.canvas.winfo_rooty()
                    if 0 <= cx < gui.canvas.winfo_width() and 0 <= cy < gui.canvas.winfo_height():
                        try:
                            event_logger.info('Forwarding global press to canvas at %s,%s', cx, cy)
                        except Exception:
                            pass
                        fakep = SimpleNamespace(x=int(cx), y=int(cy), widget=gui.canvas, x_root=wx, y_root=wy)
                        try:
                            gui._on_canvas_press(fakep)
                        except Exception:
                            pass
            except Exception:
                pass

        gui.root.bind_all('<ButtonPress-1>', _global_click, add='+')
        gui.root.bind_all('<ButtonPress-1>', _global_press_forward, add='+')
        gui.root.bind_all('<ButtonRelease-1>', _global_release_forward, add='+')
        gui.root.bind_all('<FocusIn>', lambda e: open(debug_path, 'a').write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} FOCUS IN widget={str(e.widget)}\n"), add='+')
        gui.root.bind_all('<FocusOut>', lambda e: open(debug_path, 'a').write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} FOCUS OUT widget={str(e.widget)}\n"), add='+')
    except Exception:
        pass


def schedule_ai_move(gui, delay_ms=300):
    # schedule AI work after `delay_ms` ms
    def do_ai_move():
        def worker():
            try:
                event_logger.info('AI computation started')
            except Exception:
                pass
            ai_move = None
            try:
                ai_move = gui.game.current_player.choose_move(gui.game.board)
            except Exception:
                try:
                    ai_move = gui.game.current_player.choose_move_minimax(gui.game.board, None)
                except Exception:
                    ai_move = None

            def apply_move():
                try:
                    if ai_move:
                        logger.debug('AI selected move %s', ai_move)
                        result = gui.game.play_turn(ai_move[0], ai_move[1])
                        logger.debug('AI play_turn result %s', result)
                        if result and result.get('flipped'):
                            gui.animate_flips(result.get('flipped'), result.get('mover_color'))
                        else:
                            gui.draw_board()
                            gui.update_status()
                            gui.root.after(300, gui.after_move)
                    else:
                        gui.draw_board()
                        gui.update_status()
                except Exception:
                    logger.exception('Error applying AI move')

            try:
                gui.root.after(0, apply_move)
            except Exception:
                pass
            try:
                event_logger.info('AI computation finished')
            except Exception:
                pass

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    try:
        gui.root.after(delay_ms, do_ai_move)
    except Exception:
        pass


def replay_queued_click(gui):
    try:
        # replay all queued clicks in order (small stagger) to avoid dropping any
        q = getattr(gui, '_pending_clicks', None)
        if q:
            delay = 50
            while q:
                try:
                    px, py = q.pop(0)
                    fake = SimpleNamespace(x=px, y=py, widget=gui.canvas, x_root=None, y_root=None)
                    event_logger.info('Replaying queued click at (%s,%s)', px, py)
                    gui.root.after(delay, (lambda f=fake: gui.on_click(f)))
                    delay += 50
                except Exception:
                    pass
    except Exception:
        pass
