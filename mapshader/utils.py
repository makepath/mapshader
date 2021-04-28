import numpy as np
import psutil

def find_and_set_categoricals(df):
    '''
    Experimental utility to find undefined categorical categories
    '''

    categorical_fields = []
    non_categorical_object_fields = []

    for c in df.columns:

        print(c)

        if df[c].values.dtype == 'object':

            if len(df) > 3000 and len(np.unique(df[c].head(3000).astype('str'))) <= 128:
                df[c] = df[c].astype('category')
                categorical_fields.append(c)

            elif len(df) > 1000 and len(np.unique(df[c].head(1000).astype('str'))) <= 128:
                df[c] = df[c].astype('category')
                categorical_fields.append(c)

            elif len(np.unique(df[c].astype(str))) <= 128:
                df[c] = df[c].astype('category')
                categorical_fields.append(c)

            else:
                non_categorical_object_fields.append(c)

        elif 'int' in str(df[c].values.dtype):

            if len(df) > 100 and len(np.unique(df[c])) < 20:
                df[c] = df[c].astype('category')
                categorical_fields.append(c)

    return categorical_fields, non_categorical_object_fields

def psutil_fetching():
    # CPU logs
    cpu_usage_percentage = psutil.cpu_percent(interval=1)
    cpu_number_logical = psutil.cpu_count()
    cpu_number_physical = psutil.cpu_count(logical=False)

    cpu_times = psutil.cpu_times()

    cpu_per_cpu_percentage = psutil.cpu_percent(interval=1, percpu=True)

    # Disks
    disk_usage = psutil.disk_usage("/")  # Root disk usage

    log = {
        'cpu':
            {
                'cpu_usage_percentage': cpu_usage_percentage,
                'cpu_number_logical': cpu_number_logical,
                'cpu_number_physical': cpu_number_physical,
                'cpu_per_cpu_percentage': cpu_per_cpu_percentage,
                'cpu_times': cpu_times._asdict(),
            },
        'memory': psutil.virtual_memory()._asdict(),
        'disk': disk_usage._asdict(),
    }

    return log

def psutils_html():
    return '''
        <style>
        #psutils {
            display: flex;
            gap: 8px;
        }

        .bar-main-container {
            width: 300px;
            height: 24px;
            border-radius: 4px;
            font-family: sans-serif;
            font-weight: normal;
            font-size: 0.7em;
            color: rgb(64, 64, 64);
        }

        .wrap {
            padding: 0 8px;
            position: relative;
        }

        .bar-text {
            width: calc(100% - 14px);
            position: absolute;
            display: flex;
            justify-content: center;
            top: 4.5px;
        }

        .bar-container {
            float: right;
            border-radius: 10px;
            height: 10px;
            background: rgba(0, 0, 0, 0.13);
            width: 100%;
            margin: 7px 0px;
            overflow: hidden;
        }

        .bar {
            float: left;
            background: #ffffffd1;
            height: 100%;
            border-radius: 10px 0px 0px 10px;
            opacity: 1;
            transition: width 0.1s;
            width: 0%;
        }

        /* COLORS */
        .azure {
            background: #38b1cc;
        }
        .emerald {
            background: #2cb299;
        }
        .violet {
            background: #8e5d9f;
        }
        .yellow {
            background: #efc32f;
        }
        .red {
            background: #e44c41;
        }
        </style>
        <div id="psutils">
        <div class="bar-main-container azure">
            <div class="wrap">
            <span class="bar-text">
                <span>CPU:&nbsp;</span>
                <span id="cpu-percentage">0,0%</span>
            </span>
            <div class="bar-container">
                <div id="cpu-percentage-bar" class="bar"></div>
            </div>
            </div>
        </div>
        <div class="bar-main-container violet">
            <div class="wrap">
            <span class="bar-text">
                <span>MEMORY:&nbsp;</span>
                <span id="memory-percentage">0,0%</span>
            </span>
            <div class="bar-container">
                <div id="memory-percentage-bar" class="bar"></div>
            </div>
            </div>
        </div>
        <div class="bar-main-container yellow">
            <div class="wrap">
            <span class="bar-text">
                <span>DISK:&nbsp;</span>
                <span id="disk-percentage">0,0%</span>
            </span>
            <div class="bar-container">
                <div id="disk-percentage-bar" class="bar"></div>
            </div>
            </div>
        </div>
        </div>
        <script>
        const fetchAndPopulate = async () => {
            const data = await fetch("http://localhost:5000/psutil");
            const log = await data.json();

            document.getElementById(
            "cpu-percentage"
            ).innerText = `${log.cpu.cpu_usage_percentage}%`;

            document.getElementById(
            "cpu-percentage-bar"
            ).style.width = `${log.cpu.cpu_usage_percentage}%`;

            document.getElementById(
            "memory-percentage"
            ).innerText = `${log.memory.percent}%`;

            document.getElementById(
            "memory-percentage-bar"
            ).style.width = `${log.memory.percent}%`;

            document.getElementById(
            "disk-percentage"
            ).innerText = `${log.disk.percent}%`;

            document.getElementById(
            "disk-percentage-bar"
            ).style.width = `${log.disk.percent}%`;
        };
        fetchAndPopulate();

        setInterval(fetchAndPopulate, 2000);
        </script>
    '''
