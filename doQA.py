from modules import configModule, controllerModule, interfaceModule


if __name__ == '__main__':
    try:
        configModule.init()
        interfaceModule.init()
    except Exception as e:
        print(f"Errore in fase di inizializzazione - " + str(e))
        controllerModule.manage_exit()
        exit()

    interfaceModule.start()

    controllerModule.manage_exit()
