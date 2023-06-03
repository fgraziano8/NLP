from modules import configModule, evaluationModule


if __name__ == '__main__':
    try:
        configModule.init()
    except Exception as e:
        print(f"Errore in fase di inizializzazione - " + str(e))
        exit()

    evaluationModule.start()

    evaluationModule.print_evaluation_stats()

    # evaluationModule.start_fit()

    # evaluationModule.print_evaluation_stats()

    # TEST
    # evaluationModule.read_eval_pickle()
    # evaluationModule.print_evaluation_stats()
