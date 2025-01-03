using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Level : MonoBehaviour
{
    private const float camera_ortho_size = 50f;
    private const float szerokosc_rury = 4f;
    private const float wysokosc_glowki = 1f;
    private const float szybkosc_rury = 70f;
    private const float niszczyciel_rur_x = -150f;
    private const float spawner_rur_x = 150f;
    private const float ghost_x_position = 0f;

    private static Level instance;

    public static Level GetInstance()
    {
        return instance;
    }

    private List<Pipe> pipeList;
    private int pipesPassedCount;
    private int pipesSpawned;
    private float pipeSpawnTimer;
    private float pipeSpawnTimerMax;
    private float gapSize;
    private State state;

    public enum Difficulty
    {
        Easy,
        Medium,
        Hard,
        Expert,
    }

    private enum State
    {
        WaitingToStart,
        Playing,
        GhostDead,
    }

    private void Awake()
    {
        instance = this;
        pipeList = new List<Pipe>();
        pipeSpawnTimerMax = 1f;
        SetDifficulty(Difficulty.Easy);
        state = State.WaitingToStart;
    }

    private void Start()
    {
        Duch.GetInstance().OnDied += Duch_OnDied;
        Duch.GetInstance().OnStartedPlaying += Duch_OnStartedPlaying;
    }

    private void Duch_OnStartedPlaying(object sender, System.EventArgs e)
    {
        state = State.Playing;
    }

    private void Duch_OnDied(object sender, System.EventArgs e)
    {
        Debug.Log("Unlucky trafił się egzamin z MADu");
        state = State.GhostDead;
    }

    private void Update()
    {
        if (state == State.Playing)
        {
            HandlePipeMovement();
            HandlePipeSpawn();
        }
    }

    private void HandlePipeSpawn()
    {
        pipeSpawnTimer -= Time.deltaTime;
        if (pipeSpawnTimer < 0)
        {
            pipeSpawnTimer += pipeSpawnTimerMax;

            float heightEdgeLimit = 10f;
            float minHeight = gapSize * .5f + heightEdgeLimit;
            float totalHeight = camera_ortho_size * 2f;
            float maxHeight = totalHeight - gapSize * .5f - heightEdgeLimit;

            float height = Random.Range(minHeight, maxHeight);
            CreateGapPipes(height, gapSize, spawner_rur_x);
        }
    }

    private void HandlePipeMovement()
    {
        for (int i = 0; i < pipeList.Count; i++)
        {
            Pipe pipe = pipeList[i];

            bool isToTheRightOfGhost = pipe.GetXPosition() > ghost_x_position;
            pipe.Move();

            if (isToTheRightOfGhost && pipe.GetXPosition() <= ghost_x_position && pipe.IsBottom())
            {
                pipesPassedCount++;
            }

            if (pipe.GetXPosition() < niszczyciel_rur_x)
            {
                pipe.DestroySelf();
                pipeList.Remove(pipe);
                i--;
            }
        }
    }

    private void SetDifficulty(Difficulty difficulty)
    {
        switch (difficulty)
        {
            case Difficulty.Easy:
                gapSize = 60f;
                break;
            case Difficulty.Medium:
                gapSize = 50f;
                break;
            case Difficulty.Hard:
                gapSize = 40f;
                break;
            case Difficulty.Expert:
                gapSize = 30f;
                break;
        }
    }
    private  Difficulty GetDifficulty()
    {
        if (pipesSpawned >= 30) return Difficulty.Expert;
        if (pipesSpawned >= 20) return Difficulty.Hard;
        if (pipesSpawned >= 10) return Difficulty.Medium;
        return Difficulty.Easy;
    }

    private void CreateGapPipes(float gapY, float gapSize, float xPosition)
    {
        TworzRure(gapY - gapSize * .5f, xPosition, true);
        TworzRure(camera_ortho_size * 2f - gapY - gapSize * .5f, xPosition, false);
        pipesSpawned++;
        SetDifficulty(GetDifficulty());
    }

    private void TworzRure(float height, float xPosition, bool createBottom)
    {
        Transform glowka = Instantiate(GameAssets.GetInstance().glowka1);
        float pipeHeadYPosition;
        if (createBottom)
        {
            pipeHeadYPosition = -camera_ortho_size + height - wysokosc_glowki * .5f;
        } else
        {
            pipeHeadYPosition = +camera_ortho_size - height + wysokosc_glowki * 7.0f;
        }

        glowka.position = new Vector3(xPosition, pipeHeadYPosition);

        Transform nozka = Instantiate(GameAssets.GetInstance().nozka1);
        float pipeBodyYPosition;
        if (createBottom)
        {
            pipeBodyYPosition = -camera_ortho_size;
        } else
        {
            pipeBodyYPosition = +camera_ortho_size;
            nozka.localScale = new Vector3(4, -1, 1);
        }
        nozka.position = new Vector3(xPosition, pipeBodyYPosition);

        SpriteRenderer pipeBodySpriteRenderer = nozka.GetComponent<SpriteRenderer>();
        pipeBodySpriteRenderer.size = new Vector2(szerokosc_rury, height);

        BoxCollider2D pipeBodyBoxCollider = nozka.GetComponent<BoxCollider2D>();
        pipeBodyBoxCollider.size = new Vector2(szerokosc_rury, height);
        pipeBodyBoxCollider.offset = new Vector2(0f, height * .5f);

        Pipe pipe = new Pipe(glowka, nozka, createBottom);
        pipeList.Add(pipe);
    }

    public int GetPipesSpawned()
    {
        return pipesSpawned;
    }

    public int GetPipesPassedCount()
    {
        return pipesPassedCount;
    }

    private class Pipe
    {
        private Transform pipeHeadTransform;
        private Transform pipeBodyTransform;
        private bool isBottom;

        public Pipe(Transform pipeHeadTransform, Transform pipeBodyTransform, bool isBottom)
        {
            this.pipeHeadTransform = pipeHeadTransform;
            this.pipeBodyTransform = pipeBodyTransform;
            this.isBottom = isBottom;
        }

        public void Move()
        {
            pipeHeadTransform.position += new Vector3(-1, 0, 0) * szybkosc_rury * Time.deltaTime;
            pipeBodyTransform.position += new Vector3(-1, 0, 0) * szybkosc_rury * Time.deltaTime;
        }

        public float GetXPosition()
        {
            return pipeHeadTransform.position.x;
        }

        public bool IsBottom()
        {
            return isBottom;
        }

        public void DestroySelf()
        {
            Destroy(pipeHeadTransform.gameObject);
            Destroy(pipeBodyTransform.gameObject);
        }
    }
}
